#!/usr/bin/env python3
"""
Test script for Gmail API integration.
This script sends a test email and checks if the Gmail API watch is working.
"""

import os
import sys
import json
import time
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from google.api_core.exceptions import NotFound

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

def load_credentials(token_file):
    """Load OAuth credentials from token file."""
    if not os.path.exists(token_file):
        print(f"Error: Token file {token_file} not found.")
        print("Please run gmail_auth.py first to authenticate.")
        sys.exit(1)
        
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        
    return Credentials.from_authorized_user_info(token_data)

def send_test_email(service, to_email):
    """Send a test email using Gmail API."""
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = 'Test Email for Gmail API Integration'
    
    body = """
    Hello,
    
    This is a test email to verify that the Gmail API integration is working correctly.
    
    If you receive this email, it means the sending part of the integration is working.
    
    Best regards,
    Your Auto Reply Email System
    """
    
    message.attach(MIMEText(body))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"Test email sent successfully. Message ID: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        print(f"Error sending test email: {e}")
        return None

def check_pubsub_subscription(project_id, topic_name, timeout=60):
    """Check if messages are being received on the Pub/Sub topic."""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_name = f"{topic_name}-test-sub"
    subscription_path = subscriber.subscription_path(project_id, subscription_name)
    topic_path = subscriber.topic_path(project_id, topic_name)
    
    # Create a temporary subscription if it doesn't exist
    try:
        subscriber.get_subscription(subscription=subscription_path)
        print(f"Using existing subscription: {subscription_name}")
    except NotFound:
        print(f"Creating temporary subscription: {subscription_name}")
        subscriber.create_subscription(name=subscription_path, topic=topic_path)
    
    messages_received = []
    
    def callback(message):
        print(f"Received message: {message.data}")
        messages_received.append(message.data)
        message.ack()
    
    # Start the subscriber
    print(f"Listening for messages on {subscription_name} for {timeout} seconds...")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback)
    
    # Wait for messages
    start_time = time.time()
    try:
        while time.time() - start_time < timeout and not messages_received:
            time.sleep(1)
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
    
    streaming_pull_future.cancel()
    
    if messages_received:
        print("Gmail API watch is working! Received notification(s) from Pub/Sub.")
        return True
    else:
        print("No messages received within the timeout period.")
        print("This could mean either:")
        print("1. The Gmail API watch is not working correctly")
        print("2. No new emails arrived during the test period")
        print("3. There might be a delay in the notification system")
        return False

def main():
    """Main function to test Gmail API integration."""
    token_file = 'token.json'
    test_email = 'squidgamecs2025@gmail.com'
    
    # Get project ID and topic name from command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test Gmail API integration')
    parser.add_argument('--project-id', required=True, help='Google Cloud project ID')
    parser.add_argument('--topic', required=True, help='Pub/Sub topic name for Gmail notifications')
    parser.add_argument('--wait-time', type=int, default=60, 
                        help='Time to wait for Pub/Sub messages (seconds)')
    
    args = parser.parse_args()
    
    print("Gmail API Integration Test")
    print("=========================\n")
    
    # Load credentials and create Gmail API service
    print("Loading OAuth credentials...")
    creds = load_credentials(token_file)
    service = build('gmail', 'v1', credentials=creds)
    print("Gmail API service created successfully.\n")
    
    # Send test email
    print(f"Sending test email to {test_email}...")
    message_id = send_test_email(service, test_email)
    
    if not message_id:
        print("Failed to send test email. Exiting.")
        sys.exit(1)
    
    print("\nWaiting a few seconds for the email to be processed...")
    time.sleep(5)
    
    # Check if Pub/Sub is receiving notifications
    print("\nChecking Pub/Sub for notifications...")
    check_pubsub_subscription(args.project_id, args.topic, args.wait_time)
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
