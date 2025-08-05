#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for sending test emails and verifying Auto Reply Email system

This script sends a test email and monitors for an auto-reply response,
measuring the response time and verifying the content quality.

Usage:
    python test_email.py --to=recipient@example.com [--project-id=your-project-id] [options]
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, List

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
DEFAULT_TOKEN_FILE = 'token.json'
DEFAULT_SUBJECT = 'Test Email for Auto Reply System'
DEFAULT_BODY = 'This is a test email to verify the Auto Reply Email system is working correctly.'
SECRET_NAME = 'gmail-oauth-token'


def load_credentials_from_file(token_file: str) -> Optional[Credentials]:
    """Load OAuth credentials from token file.
    
    Args:
        token_file (str): Path to token file
        
    Returns:
        Optional[Credentials]: OAuth credentials or None if not found
    """
    if not os.path.exists(token_file):
        print(f"Error: {token_file} not found. Run gmail_auth.py first.")
        return None
    
    try:
        with open(token_file, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data)
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            return creds
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading token file: {e}")
        return None
    except RefreshError as e:
        print(f"Error refreshing token: {e}")
        return None


def load_credentials_from_secret_manager(project_id: str) -> Optional[Credentials]:
    """Load OAuth credentials from Secret Manager.
    
    Args:
        project_id (str): GCP project ID
        
    Returns:
        Optional[Credentials]: OAuth credentials or None if not found
    """
    try:
        # Create Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{SECRET_NAME}/versions/latest"
        
        # Access the secret
        response = client.access_secret_version(request={"name": name})
        creds_data = json.loads(response.payload.data.decode("UTF-8"))
        
        # Create credentials
        creds = Credentials.from_authorized_user_info(creds_data)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        return creds
    except Exception as e:
        print(f"Error loading credentials from Secret Manager: {e}")
        return None


def create_message(sender: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """Create an email message.
    
    Args:
        sender (str): Sender email address
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        Dict[str, Any]: Email message object
    """
    message = MIMEText(body)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    message['date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
    
    return {
        'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()
    }


def send_test_email(service, sender: str, to: str, subject: str, body: str) -> Optional[Dict[str, Any]]:
    """Send a test email.
    
    Args:
        service: Gmail API service
        sender (str): Sender email address
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        Optional[Dict[str, Any]]: Send response or None if failed
    """
    try:
        message = create_message(sender, to, subject, body)
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"Message sent! ID: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        if error.resp.status == 403:
            print("Permission denied. Make sure the Gmail API is enabled and the account has proper permissions.")
        elif error.resp.status == 429:
            print("Rate limit exceeded. Try again later.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def extract_email_body(message: Dict[str, Any]) -> str:
    """Extract email body from message.
    
    Args:
        message (Dict[str, Any]): Gmail API message object
        
    Returns:
        str: Email body text
    """
    body = ""
    
    if 'parts' in message['payload']:
        # Multipart email
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body_bytes = base64.urlsafe_b64decode(part['body']['data'])
                    body = body_bytes.decode('utf-8')
                    break
    elif 'body' in message['payload'] and 'data' in message['payload']['body']:
        # Simple email
        body_bytes = base64.urlsafe_b64decode(message['payload']['body']['data'])
        body = body_bytes.decode('utf-8')
    
    return body


def check_for_reply(service, query: str, wait_time: int = 60, check_interval: int = 5) -> Optional[Dict[str, Any]]:
    """Check for reply to the test email.
    
    Args:
        service: Gmail API service
        query (str): Search query
        wait_time (int): Maximum wait time in seconds
        check_interval (int): Check interval in seconds
        
    Returns:
        Optional[Dict[str, Any]]: Reply message if found, None otherwise
    """
    print(f"Waiting for reply (max {wait_time} seconds)...")
    
    start_time = time.time()
    last_dot_time = 0
    
    while time.time() - start_time < wait_time:
        try:
            # Print progress dots every check_interval
            current_time = time.time()
            if current_time - last_dot_time >= check_interval:
                print(".", end="", flush=True)
                last_dot_time = current_time
            
            # Search for replies
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Limit results to most recent messages
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                # Check messages to find replies
                for msg_ref in messages:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg_ref['id']
                    ).execute()
                    
                    # Check if it's a reply (not our original message)
                    headers = message['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                    
                    if subject.startswith('Re:'):
                        response_time = time.time() - start_time
                        print(f"\n✅ Reply received in {response_time:.2f} seconds!")
                        
                        # Extract body
                        body = extract_email_body(message)
                        
                        return {
                            'id': message['id'],
                            'subject': subject,
                            'body': body,
                            'time_taken': response_time
                        }
            
            # Short sleep to avoid hitting API rate limits
            time.sleep(0.5)
            
        except HttpError as error:
            print(f"\nError checking for reply: {error}")
            if error.resp.status == 429:
                print("Rate limit exceeded. Waiting longer between checks...")
                time.sleep(check_interval * 2)  # Wait longer on rate limit
            continue
        except Exception as e:
            print(f"\nUnexpected error checking for reply: {e}")
            continue
    
    print("\n❌ No reply received within the wait time.")
    return None


def analyze_reply_content(body: str) -> Dict[str, Any]:
    """Analyze the content of the reply for quality assessment.
    
    Args:
        body (str): Reply body text
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    results = {
        'word_count': len(body.split()),
        'has_greeting': any(greeting in body.lower() for greeting in ['hello', 'hi', 'dear', 'terima kasih', 'selamat']),
        'has_signature': any(sig in body.lower() for sig in ['regards', 'sincerely', 'thank you', 'terima kasih']),
        'is_personalized': False,  # Basic check, would need more context for better assessment
        'sentiment': 'neutral'  # Simple placeholder, would need NLP for real sentiment
    }
    
    # Simple sentiment check
    positive_words = ['thank', 'happy', 'glad', 'appreciate', 'good', 'great', 'excellent']
    negative_words = ['sorry', 'issue', 'problem', 'concern', 'apologize', 'unfortunately']
    
    pos_count = sum(1 for word in positive_words if word in body.lower())
    neg_count = sum(1 for word in negative_words if word in body.lower())
    
    if pos_count > neg_count:
        results['sentiment'] = 'positive'
    elif neg_count > pos_count:
        results['sentiment'] = 'negative'
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Auto Reply Email system')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--project-id', help='GCP project ID for Secret Manager')
    parser.add_argument('--token-file', default=DEFAULT_TOKEN_FILE, help='Path to OAuth token file')
    parser.add_argument('--subject', default=DEFAULT_SUBJECT, help='Email subject')
    parser.add_argument('--body', default=DEFAULT_BODY, help='Email body')
    parser.add_argument('--wait', type=int, default=60, help='Maximum wait time for reply (seconds)')
    parser.add_argument('--check-interval', type=int, default=5, help='Check interval for replies (seconds)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Load credentials
    creds = None
    if args.project_id:
        print(f"Loading credentials from Secret Manager in project {args.project_id}...")
        creds = load_credentials_from_secret_manager(args.project_id)
    
    if not creds:
        print(f"Loading credentials from file {args.token_file}...")
        creds = load_credentials_from_file(args.token_file)
    
    if not creds:
        print("Failed to load credentials. Please run gmail_auth.py first.")
        sys.exit(1)
    
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
        if args.verbose:
            print(f"Body: {args.body}")
        
        # Send test email
        print("\n📤 Sending test email...")
        sent_message = send_test_email(service, sender, args.to, args.subject, args.body)
        if not sent_message:
            print("Failed to send test email.")
            sys.exit(1)
        
        # Check for reply
        print("\n📥 Checking for auto-reply...")
        query = f"subject:Re: {args.subject}"
        reply = check_for_reply(service, query, args.wait, args.check_interval)
        
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
            
            return True
        else:
            print("\n❌ Test failed: No auto-reply received.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
