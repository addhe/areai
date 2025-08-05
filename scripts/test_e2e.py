#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
End-to-end test script for the Auto Reply Email system

This script tests the complete flow of the Auto Reply Email system by:
1. Sending a test email
2. Verifying the Pub/Sub notification is received
3. Checking that the Cloud Function is triggered
4. Confirming an auto-reply is sent

Usage:
    python test_e2e.py --project-id=your-project-id --to=recipient@example.com [options]
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from google.auth.transport.requests import Request
from google.cloud import pubsub_v1
from google.cloud import logging as cloud_logging
from google.cloud.functions_v1 import CloudFunctionsServiceClient
from google.cloud.secretmanager import SecretManagerServiceClient
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import the test_email module to reuse its functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_email import (
    load_credentials_from_file,
    load_credentials_from_secret_manager,
    send_test_email,
    check_for_reply,
    analyze_reply_content
)

# Constants
DEFAULT_TOKEN_FILE = 'token.json'
DEFAULT_SUBJECT = 'E2E Test for Auto Reply System'
DEFAULT_BODY = """
Hello,

This is an end-to-end test email for the Auto Reply Email system.
Please process this email and send an automated response.

Thank you,
E2E Test
"""
DEFAULT_WAIT_TIME = 120  # seconds
DEFAULT_FUNCTION_NAME = 'process-email'
DEFAULT_PUBSUB_TOPIC = 'gmail-notifications'
DEFAULT_OAUTH_SECRET = 'gmail-oauth-token'


def check_pubsub_notification(project_id: str, topic_name: str, 
                             start_time: datetime, 
                             timeout: int = 60) -> Optional[Dict[str, Any]]:
    """Check for Pub/Sub notification from Gmail API.
    
    Args:
        project_id (str): GCP project ID
        topic_name (str): Pub/Sub topic name
        start_time (datetime): Start time to check for notifications
        timeout (int): Maximum wait time in seconds
        
    Returns:
        Optional[Dict[str, Any]]: Notification data if found, None otherwise
    """
    print(f"Checking for Pub/Sub notifications on topic {topic_name}...")
    
    # Create a Pub/Sub subscriber client
    subscriber = pubsub_v1.SubscriberClient()
    
    # Create a temporary subscription to the topic
    subscription_path = subscriber.subscription_path(
        project_id, f"e2e-test-sub-{int(time.time())}"
    )
    topic_path = subscriber.topic_path(project_id, topic_name)
    
    try:
        # Create subscription with filter for messages after start_time
        subscription = subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "filter": f"attributes.publishTime >= \"{start_time.isoformat()}Z\""
            }
        )
        
        print(f"Created temporary subscription: {subscription.name}")
        
        # Wait for messages
        messages = []
        
        def callback(message):
            messages.append(message)
            message.ack()
            
        streaming_pull_future = subscriber.subscribe(subscription_path, callback)
        
        # Wait for messages
        end_time = time.time() + timeout
        while time.time() < end_time and not messages:
            print(".", end="", flush=True)
            time.sleep(2)
            
        streaming_pull_future.cancel()
        
        if messages:
            print(f"\nReceived {len(messages)} Pub/Sub notification(s)")
            # Parse the first message
            message = messages[0]
            data = json.loads(message.data.decode('utf-8'))
            return {
                'data': data,
                'attributes': dict(message.attributes),
                'publish_time': message.publish_time
            }
        else:
            print("\nNo Pub/Sub notifications received within timeout")
            return None
            
    except Exception as e:
        print(f"Error checking Pub/Sub notifications: {e}")
        return None
    finally:
        # Clean up the temporary subscription
        try:
            subscriber.delete_subscription(request={"subscription": subscription_path})
            print(f"Deleted temporary subscription: {subscription_path}")
        except Exception as e:
            print(f"Error deleting subscription: {e}")


def check_cloud_function_execution(project_id: str, function_name: str, 
                                  region: str, start_time: datetime,
                                  timeout: int = 60) -> Optional[Dict[str, Any]]:
    """Check if Cloud Function was executed.
    
    Args:
        project_id (str): GCP project ID
        function_name (str): Cloud Function name
        region (str): GCP region
        start_time (datetime): Start time to check for executions
        timeout (int): Maximum wait time in seconds
        
    Returns:
        Optional[Dict[str, Any]]: Execution data if found, None otherwise
    """
    print(f"Checking for Cloud Function execution of {function_name}...")
    
    # Create Cloud Functions client
    client = CloudFunctionsServiceClient()
    
    # Format the function name
    function_path = f"projects/{project_id}/locations/{region}/functions/{function_name}"
    
    # Create Cloud Logging client to check logs
    logging_client = cloud_logging.Client(project=project_id)
    
    # Convert start_time to RFC3339 format
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Build the filter
    filter_str = (
        f'resource.type="cloud_function" '
        f'resource.labels.function_name="{function_name}" '
        f'resource.labels.region="{region}" '
        f'timestamp>="{start_time_str}"'
    )
    
    end_time = time.time() + timeout
    execution_found = False
    execution_data = None
    
    while time.time() < end_time and not execution_found:
        print(".", end="", flush=True)
        
        # Query logs
        try:
            logger = logging_client.logger('cloudfunctions.googleapis.com%2Fcloud-functions')
            entries = logger.list_entries(
                filter_=filter_str,
                order_by="timestamp desc",
                max_results=10
            )
            
            # Check entries
            for entry in entries:
                execution_found = True
                execution_data = {
                    'timestamp': entry.timestamp,
                    'severity': entry.severity,
                    'payload': entry.payload,
                    'resource': entry.resource.labels,
                    'labels': entry.labels
                }
                break
                
            if execution_found:
                break
                
            time.sleep(5)
            
        except Exception as e:
            print(f"\nError checking Cloud Function logs: {e}")
            time.sleep(5)
    
    if execution_found:
        print(f"\nCloud Function execution found at {execution_data['timestamp']}")
        return execution_data
    else:
        print("\nNo Cloud Function execution found within timeout")
        return None


def verify_secret_manager_setup(project_id: str, secret_id: str) -> bool:
    """Verify Secret Manager is properly set up with OAuth token.
    
    Args:
        project_id (str): GCP project ID
        secret_id (str): Secret ID for OAuth token
        
    Returns:
        bool: True if secret exists and is valid, False otherwise
    """
    print(f"Verifying Secret Manager setup for {secret_id}...")
    
    try:
        # Create Secret Manager client
        client = SecretManagerServiceClient()
        
        # Format the secret name
        secret_name = f"projects/{project_id}/secrets/{secret_id}"
        
        # Try to access the secret
        try:
            client.get_secret(request={"name": secret_name})
            print(f"✅ Secret {secret_id} exists")
            
            # Check if the secret has versions
            versions = list(client.list_secret_versions(request={"parent": secret_name}))
            if versions:
                print(f"✅ Secret {secret_id} has {len(versions)} version(s)")
                
                # Try to access the latest version
                latest_version = f"{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": latest_version})
                
                # Validate it's a JSON token
                try:
                    token_data = json.loads(response.payload.data.decode("UTF-8"))
                    required_fields = ["token", "refresh_token", "token_uri", "client_id", "client_secret"]
                    missing_fields = [field for field in required_fields if field not in token_data]
                    
                    if not missing_fields:
                        print(f"✅ Secret {secret_id} contains valid OAuth token data")
                        return True
                    else:
                        print(f"❌ Secret {secret_id} is missing required fields: {', '.join(missing_fields)}")
                        return False
                except json.JSONDecodeError:
                    print(f"❌ Secret {secret_id} does not contain valid JSON data")
                    return False
            else:
                print(f"❌ Secret {secret_id} exists but has no versions")
                return False
                
        except Exception:
            print(f"❌ Secret {secret_id} does not exist")
            return False
            
    except Exception as e:
        print(f"Error verifying Secret Manager setup: {e}")
        return False


def run_e2e_test(args) -> bool:
    """Run the end-to-end test.
    
    Args:
        args: Command line arguments
        
    Returns:
        bool: True if test passed, False otherwise
    """
    # Record start time for all checks
    start_time = datetime.utcnow()
    
    # Step 1: Verify Secret Manager setup
    if args.check_secret:
        secret_ok = verify_secret_manager_setup(args.project_id, args.oauth_secret)
        if not secret_ok and not args.ignore_failures:
            print("❌ Secret Manager verification failed. Aborting test.")
            return False
    
    # Step 2: Load credentials
    creds = None
    if args.use_secret_manager:
        print(f"Loading credentials from Secret Manager in project {args.project_id}...")
        creds = load_credentials_from_secret_manager(args.project_id)
    
    if not creds:
        print(f"Loading credentials from file {args.token_file}...")
        creds = load_credentials_from_file(args.token_file)
    
    if not creds:
        print("Failed to load credentials. Please run gmail_auth.py first.")
        return False
    
    try:
        # Build Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # Get sender email (from profile)
        profile = service.users().getProfile(userId='me').execute()
        sender = profile['emailAddress']
        
        print("\n📧 Test Email Configuration:")
        print(f"From: {sender}")
        print(f"To: {args.to}")
        print(f"Subject: {args.subject}")
        
        # Step 3: Send test email
        print("\n📤 Sending test email...")
        sent_message = send_test_email(service, sender, args.to, args.subject, args.body)
        if not sent_message:
            print("❌ Failed to send test email.")
            return False
        
        # Step 4: Check for Pub/Sub notification
        if args.check_pubsub:
            pubsub_result = check_pubsub_notification(
                args.project_id, 
                args.pubsub_topic,
                start_time,
                args.wait
            )
            
            if not pubsub_result and not args.ignore_failures:
                print("❌ No Pub/Sub notification received. Aborting test.")
                return False
        
        # Step 5: Check for Cloud Function execution
        if args.check_function:
            function_result = check_cloud_function_execution(
                args.project_id,
                args.function_name,
                args.region,
                start_time,
                args.wait
            )
            
            if not function_result and not args.ignore_failures:
                print("❌ No Cloud Function execution detected. Aborting test.")
                return False
        
        # Step 6: Check for reply
        print("\n📥 Checking for auto-reply...")
        query = f"subject:Re: {args.subject}"
        reply = check_for_reply(service, query, args.wait)
        
        if reply:
            print("\n📋 Reply Analysis:")
            print(f"Subject: {reply['subject']}")
            if args.verbose:
                print(f"Body:\n{reply['body']}")
            else:
                # Show first 100 chars if not verbose
                preview = reply['body'][:100] + "..." if len(reply['body']) > 100 else reply['body']
                print(f"Body preview: {preview}")
            
            # Check if response time meets requirement
            if reply['time_taken'] <= 15:
                print(f"✅ Response time: {reply['time_taken']:.2f} seconds (meets <15 second requirement)")
            else:
                print(f"❌ Response time: {reply['time_taken']:.2f} seconds (exceeds <15 second requirement)")
            
            # Analyze content
            analysis = analyze_reply_content(reply['body'])
            print("\n📊 Content Quality Metrics:")
            print(f"Word count: {analysis['word_count']}")
            print(f"Has greeting: {'✅' if analysis['has_greeting'] else '❌'}")
            print(f"Has signature: {'✅' if analysis['has_signature'] else '❌'}")
            print(f"Sentiment: {analysis['sentiment']}")
            
            # Print overall test result
            print("\n🎯 End-to-End Test Result:")
            print("✅ Test completed successfully!")
            return True
        else:
            print("\n❌ Test failed: No auto-reply received.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='End-to-End Test for Auto Reply Email system')
    
    # Required arguments
    parser.add_argument('--project-id', required=True, help='GCP project ID')
    parser.add_argument('--to', required=True, help='Recipient email address')
    
    # Optional arguments
    parser.add_argument('--region', default='us-central1', help='GCP region')
    parser.add_argument('--token-file', default=DEFAULT_TOKEN_FILE, help='Path to OAuth token file')
    parser.add_argument('--subject', default=DEFAULT_SUBJECT, help='Email subject')
    parser.add_argument('--body', default=DEFAULT_BODY, help='Email body')
    parser.add_argument('--wait', type=int, default=DEFAULT_WAIT_TIME, help='Maximum wait time (seconds)')
    parser.add_argument('--function-name', default=DEFAULT_FUNCTION_NAME, help='Cloud Function name')
    parser.add_argument('--pubsub-topic', default=DEFAULT_PUBSUB_TOPIC, help='Pub/Sub topic name')
    parser.add_argument('--oauth-secret', default=DEFAULT_OAUTH_SECRET, help='OAuth token secret name')
    
    # Feature flags
    parser.add_argument('--use-secret-manager', action='store_true', help='Load credentials from Secret Manager')
    parser.add_argument('--check-pubsub', action='store_true', help='Check for Pub/Sub notifications')
    parser.add_argument('--check-function', action='store_true', help='Check for Cloud Function execution')
    parser.add_argument('--check-secret', action='store_true', help='Verify Secret Manager setup')
    parser.add_argument('--ignore-failures', action='store_true', help='Continue test even if steps fail')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    print("🧪 Starting End-to-End Test for Auto Reply Email System")
    print(f"Project ID: {args.project_id}")
    print(f"Region: {args.region}")
    
    success = run_e2e_test(args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
