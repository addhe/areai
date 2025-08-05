#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
End-to-end test script for Auto Reply Email system
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def run_command(cmd, capture_output=True):
    """Run a shell command.
    
    Args:
        cmd (str): Command to run
        capture_output (bool): Whether to capture output
        
    Returns:
        str: Command output if capture_output is True
    """
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture_output,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
        
    return result.stdout if capture_output else None


def load_credentials(token_file):
    """Load OAuth credentials from token file.
    
    Args:
        token_file (str): Path to token file
        
    Returns:
        Credentials: OAuth credentials
    """
    if not os.path.exists(token_file):
        print(f"Error: {token_file} not found. Run gmail_auth.py first.")
        return None
    
    with open(token_file, 'r') as token:
        creds_data = json.load(token)
        creds = Credentials.from_authorized_user_info(creds_data)
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds


def create_message(sender, to, subject, body):
    """Create an email message.
    
    Args:
        sender (str): Sender email address
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        dict: Email message object
    """
    from email.mime.text import MIMEText
    
    message = MIMEText(body)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    return {
        'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()
    }


def send_test_email(service, sender, to, subject, body):
    """Send a test email.
    
    Args:
        service: Gmail API service
        sender (str): Sender email address
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        dict: Send response
    """
    try:
        message = create_message(sender, to, subject, body)
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"Message sent! ID: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def check_for_reply(service, query, wait_time=60, check_interval=5):
    """Check for reply to the test email.
    
    Args:
        service: Gmail API service
        query (str): Search query
        wait_time (int): Maximum wait time in seconds
        check_interval (int): Check interval in seconds
        
    Returns:
        dict: Reply message if found, None otherwise
    """
    print(f"Waiting for reply (max {wait_time} seconds)...")
    
    start_time = time.time()
    while time.time() - start_time < wait_time:
        try:
            # Search for replies
            results = service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                # Get the most recent message
                message = service.users().messages().get(
                    userId='me',
                    id=messages[0]['id']
                ).execute()
                
                # Check if it's a reply (not our original message)
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                
                if subject.startswith('Re:'):
                    print("\nReply received!")
                    print(f"Time taken: {time.time() - start_time:.2f} seconds")
                    
                    # Extract body
                    body = ""
                    if 'parts' in message['payload']:
                        for part in message['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                if 'data' in part['body']:
                                    body_bytes = base64.urlsafe_b64decode(part['body']['data'])
                                    body = body_bytes.decode('utf-8')
                                    break
                    elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                        body_bytes = base64.urlsafe_b64decode(message['payload']['body']['data'])
                        body = body_bytes.decode('utf-8')
                    
                    return {
                        'id': message['id'],
                        'subject': subject,
                        'body': body,
                        'time_taken': time.time() - start_time
                    }
            
            print(".", end="", flush=True)
            time.sleep(check_interval)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    print("\nNo reply received within the wait time.")
    return None


def check_cloud_function_logs(project_id, function_name, minutes=5):
    """Check Cloud Function logs.
    
    Args:
        project_id (str): GCP project ID
        function_name (str): Cloud Function name
        minutes (int): Number of minutes to check
        
    Returns:
        list: Log entries
    """
    print(f"Checking Cloud Function logs for the last {minutes} minutes...")
    
    cmd = f"gcloud logging read 'resource.type=cloud_function AND resource.labels.function_name={function_name}' --project={project_id} --limit=50 --format=json"
    
    try:
        logs_json = run_command(cmd)
        logs = json.loads(logs_json)
        
        if not logs:
            print("No logs found")
            return []
        
        print(f"Found {len(logs)} log entries")
        return logs
    except Exception as e:
        print(f"Error checking logs: {str(e)}")
        return []


def test_pubsub_trigger(project_id, topic_name, history_id="12345"):
    """Test Pub/Sub trigger directly.
    
    Args:
        project_id (str): GCP project ID
        topic_name (str): Pub/Sub topic name
        history_id (str): History ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("Testing Pub/Sub trigger directly...")
    
    # Create message
    message = {
        "historyId": history_id,
        "emailAddress": "test@example.com"
    }
    
    # Encode message
    encoded_message = base64.b64encode(json.dumps(message).encode()).decode()
    
    # Publish message
    cmd = f"gcloud pubsub topics publish {topic_name} --message='{encoded_message}' --project={project_id}"
    
    try:
        run_command(cmd)
        print("Message published successfully")
        return True
    except Exception as e:
        print(f"Error publishing message: {str(e)}")
        return False


def run_integration_tests(project_dir):
    """Run integration tests.
    
    Args:
        project_dir (str): Project directory
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("Running integration tests...")
    
    cmd = f"cd {project_dir} && python -m pytest tests/integration/ -v"
    
    try:
        run_command(cmd, capture_output=False)
        print("Integration tests passed")
        return True
    except Exception:
        print("Integration tests failed")
        return False


def run_unit_tests(project_dir):
    """Run unit tests.
    
    Args:
        project_dir (str): Project directory
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("Running unit tests...")
    
    cmd = f"cd {project_dir} && python -m pytest tests/unit/ -v"
    
    try:
        run_command(cmd, capture_output=False)
        print("Unit tests passed")
        return True
    except Exception:
        print("Unit tests failed")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="End-to-end test for Auto Reply Email system")
    parser.add_argument("--project-id", help="GCP project ID")
    parser.add_argument("--token-file", default="token.json", help="Path to OAuth token file")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--subject", default="Test Email for Auto Reply System", help="Email subject")
    parser.add_argument("--body", default="This is a test email to verify the Auto Reply Email system is working correctly.", help="Email body")
    parser.add_argument("--wait", type=int, default=60, help="Maximum wait time for reply (seconds)")
    parser.add_argument("--skip-email", action="store_true", help="Skip email test")
    parser.add_argument("--skip-pubsub", action="store_true", help="Skip Pub/Sub test")
    parser.add_argument("--skip-unit-tests", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-integration-tests", action="store_true", help="Skip integration tests")
    
    args = parser.parse_args()
    
    # Get project ID
    project_id = args.project_id
    if not project_id:
        try:
            project_id = run_command("gcloud config get-value project").strip()
        except Exception:
            project_id = input("Enter your GCP project ID: ")
    
    # Resolve paths
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent
    token_file = args.token_file
    if not os.path.isabs(token_file):
        token_file = script_dir / token_file
    
    # Print test information
    print("=" * 80)
    print("Auto Reply Email System - End-to-End Test")
    print("=" * 80)
    print(f"Project ID: {project_id}")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Run unit tests
    if not args.skip_unit_tests:
        unit_tests_passed = run_unit_tests(project_dir)
        print("-" * 80)
    else:
        unit_tests_passed = True
    
    # Run integration tests
    if not args.skip_integration_tests:
        integration_tests_passed = run_integration_tests(project_dir)
        print("-" * 80)
    else:
        integration_tests_passed = True
    
    # Test Pub/Sub trigger
    if not args.skip_pubsub:
        pubsub_test_passed = test_pubsub_trigger(project_id, "new-email")
        print("-" * 80)
    else:
        pubsub_test_passed = True
    
    # Test email flow
    email_test_passed = True
    if not args.skip_email:
        if not args.to:
            print("Error: Recipient email address required for email test")
            email_test_passed = False
        else:
            # Load credentials
            creds = load_credentials(token_file)
            if not creds:
                email_test_passed = False
            else:
                # Build Gmail API service
                service = build('gmail', 'v1', credentials=creds)
                
                # Get sender email
                profile = service.users().getProfile(userId='me').execute()
                sender = profile['emailAddress']
                
                print(f"Sending test email from {sender} to {args.to}")
                print(f"Subject: {args.subject}")
                print(f"Body: {args.body}")
                
                # Send test email
                sent_message = send_test_email(service, sender, args.to, args.subject, args.body)
                if not sent_message:
                    email_test_passed = False
                else:
                    # Check for reply
                    query = f"subject:Re: {args.subject}"
                    reply = check_for_reply(service, query, args.wait)
                    
                    if reply:
                        print("\nReply details:")
                        print(f"Subject: {reply['subject']}")
                        print(f"Body: {reply['body']}")
                        print(f"Response time: {reply['time_taken']:.2f} seconds")
                        
                        # Check if response time meets requirement
                        if reply['time_taken'] <= 15:
                            print("✅ Response time meets requirement (<15 seconds)")
                        else:
                            print("❌ Response time exceeds requirement (>15 seconds)")
                            email_test_passed = False
                    else:
                        print("❌ No reply received")
                        email_test_passed = False
        
        print("-" * 80)
    
    # Check Cloud Function logs
    logs = check_cloud_function_logs(project_id, "auto-reply-email")
    
    # Print test summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Unit Tests: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_tests_passed else '❌ FAILED'}")
    print(f"Pub/Sub Test: {'✅ PASSED' if pubsub_test_passed else '❌ FAILED'}")
    print(f"Email Test: {'✅ PASSED' if email_test_passed else '❌ FAILED'}")
    print("-" * 80)
    
    all_passed = unit_tests_passed and integration_tests_passed and pubsub_test_passed and email_test_passed
    print(f"Overall Result: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
