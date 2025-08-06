#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail API OAuth authentication script for Auto Reply Email system

This script handles the OAuth 2.0 flow for Gmail API authentication,
saves the token securely, and sets up Gmail API watch for new emails.

Usage:
    python gmail_auth.py --project-id=your-project-id [--credentials-file=path/to/credentials.json] [--token-file=path/to/token.json]
"""

import argparse
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]
DEFAULT_CREDENTIALS_FILE = 'client_secret.json'
DEFAULT_TOKEN_FILE = 'token.json'
SECRET_NAME = 'gmail-oauth-token'


def authenticate_gmail(credentials_file, token_file):
    """Authenticate with Gmail API using OAuth 2.0.
    
    Args:
        credentials_file (str): Path to OAuth client credentials file
        token_file (str): Path to save/load OAuth token
    
    Returns:
        Credentials: OAuth 2.0 credentials
        
    Raises:
        FileNotFoundError: If credentials file doesn't exist
        RefreshError: If token refresh fails
    """
    creds = None
    
    # Check if token file exists
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as token:
                token_data = json.load(token)
                creds = Credentials.from_authorized_user_info(token_data)
                print(f"Loaded existing token for account: {token_data.get('client_id', 'unknown')}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading token file: {e}")
            print("Will create a new token.")
            creds = None
    
    # If credentials exist but are expired, refresh them
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("Token refreshed successfully.")
        except RefreshError as e:
            print(f"Error refreshing token: {e}")
            print("Will create a new token.")
            creds = None
    
    # If no valid credentials, authenticate
    if not creds:
        if not os.path.exists(credentials_file):
            print(f"Error: {credentials_file} not found.")
            print("Please download OAuth 2.0 Client ID credentials from Google Cloud Console:")
            print("https://console.cloud.google.com/apis/credentials")
            raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
        
        print("\n==== IMPORTANT: OAUTH CONFIGURATION CHECK ====\n")
        print("Your OAuth client should be configured with the following redirect URI:")
        print("   - http://localhost:4443/")
        print("\nPlease verify this is configured in your Google Cloud Console:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Find and edit your OAuth client ID")
        print("3. Make sure the above redirect URI is listed")
        print("4. Save any changes if needed\n")
        
        proceed = input("Is your OAuth client configured with http://localhost:4443/ as a redirect URI? (yes/no): ")
        if proceed.lower() != 'yes':
            print("Please update your OAuth configuration and run this script again.")
            sys.exit(0)
        
        try:
            # Check if port 8080 is already in use
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port_available = True
            try:
                sock.bind(('localhost', 4443))
            except socket.error:
                port_available = False
            finally:
                sock.close()
            
            if not port_available:
                print("\nWARNING: Port 4443 is already in use!")
                print("Please free up port 4443 by stopping any services using it and try again.")
                print("You can find what's using port 4443 with: lsof -i :4443")
                print("And stop the process with: kill <PID>")
                sys.exit(1)
            
            # Use the local server flow
            print("\nStarting authentication with local server...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=4443)
            print("Authentication successful!")
            
            # Ensure we have offline access (refresh token)
            if not creds.refresh_token:
                print("\nWARNING: No refresh token obtained. This may cause issues with long-term access.")
                print("This typically happens if you've already authorized this application.")
                print("To fix this, revoke access in your Google Account and try again:")
                print("https://myaccount.google.com/permissions")
                proceed = input("\nDo you want to continue anyway? (yes/no): ")
                if proceed.lower() != 'yes':
                    sys.exit(0)
            
            # Save the credentials for the next run
            token_dir = os.path.dirname(token_file)
            if token_dir and not os.path.exists(token_dir):
                os.makedirs(token_dir)
                
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
                print(f"\nToken saved to {token_file}")
                
        except Exception as e:
            print(f"\nError during authentication: {e}")
            raise
    
    return creds


def setup_gmail_watch(creds, topic_name):
    """Set up Gmail API watch for new emails.
    
    Args:
        creds: OAuth 2.0 credentials
        topic_name (str): Pub/Sub topic name
        
    Returns:
        dict: Watch response with expiration and historyId
        
    Raises:
        HttpError: If the API request fails
    """
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name
        }
        
        response = service.users().watch(userId='me', body=request).execute()
        
        # Convert expiration from microseconds since epoch to human-readable format
        expiration_ms = int(response['expiration']) / 1000
        expiration_date = datetime.fromtimestamp(expiration_ms)
        
        print(f"Watch setup successfully.")
        print(f"Expiration: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Initial history ID: {response['historyId']}")
        
        # Calculate days until expiration
        days_valid = (expiration_date - datetime.now()).days
        print(f"Watch will be valid for approximately {days_valid} days")
        
        return response
        
    except HttpError as e:
        print(f"Error setting up Gmail watch: {e}")
        if e.resp.status == 403:
            print("Permission denied. Make sure the Gmail API is enabled and the account has proper permissions.")
        elif e.resp.status == 400:
            print("Invalid request. Make sure the Pub/Sub topic exists and is properly formatted.")
        raise


def save_to_secret_manager(project_id, token_file):
    """Save token to Secret Manager.
    
    Args:
        project_id (str): GCP project ID
        token_file (str): Path to OAuth token file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(token_file):
        print(f"Error: {token_file} not found.")
        return False
    
    try:
        # Create Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        
        # Check if secret already exists
        try:
            client.get_secret(request={"name": f"{parent}/secrets/{SECRET_NAME}"})
            secret_exists = True
            print(f"Secret {SECRET_NAME} already exists.")
        except Exception:
            secret_exists = False
        
        # Create secret if it doesn't exist
        if not secret_exists:
            print(f"Creating secret {SECRET_NAME}...")
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": SECRET_NAME,
                    "secret": {"replication": {"automatic": {}}}
                }
            )
        
        # Read token file
        with open(token_file, 'r') as f:
            token_data = f.read()
        
        # Add new secret version
        secret_path = f"{parent}/secrets/{SECRET_NAME}"
        response = client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": token_data.encode("UTF-8")}
            }
        )
        
        print(f"Token saved to Secret Manager: {response.name}")
        return True
        
    except Exception as e:
        print(f"Error saving to Secret Manager: {e}")
        print("\nAlternatively, you can save the token manually with these commands:")
        print(f"gcloud secrets create {SECRET_NAME} --replication-policy=automatic")
        print(f"gcloud secrets versions add {SECRET_NAME} --data-file={token_file}")
        return False


def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Gmail API OAuth authentication for Auto Reply Email system")
    parser.add_argument(
        "--project-id", 
        default=os.getenv('GCP_PROJECT_ID'),
        help="GCP project ID (default: from .env)"
    )
    parser.add_argument(
        "--credentials-file", 
        default=DEFAULT_CREDENTIALS_FILE,
        help=f"Path to OAuth client credentials JSON file (default: {DEFAULT_CREDENTIALS_FILE})"
    )
    parser.add_argument(
        "--token-file", 
        default=DEFAULT_TOKEN_FILE,
        help=f"Path to save/load OAuth token (default: {DEFAULT_TOKEN_FILE})"
    )
    parser.add_argument(
        "--topic", 
        help="Pub/Sub topic name for Gmail watch (format: projects/{project_id}/topics/{topic})"
    )
    parser.add_argument(
        "--save-to-secret-manager",
        action="store_true",
        help="Save token to Secret Manager"
    )
    
    return parser.parse_args()


def validate_topic_name(topic_name, project_id):
    """Validate Pub/Sub topic name format.
    
    Args:
        topic_name (str): Topic name to validate
        project_id (str): GCP project ID
        
    Returns:
        str: Validated topic name
    """
    if not topic_name.startswith("projects/"):
        # Add project prefix if not present
        topic_name = f"projects/{project_id}/topics/{topic_name}"
    
    # Validate format
    parts = topic_name.split('/')
    if len(parts) != 4 or parts[0] != "projects" or parts[2] != "topics":
        print("Invalid topic name format. Expected: projects/{project_id}/topics/{topic}")
        return None
    
    return topic_name


def main():
    """Main function."""
    print("Gmail API OAuth Authentication")
    print("=============================")
    
    # Load environment variables from .env
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Authenticate with Gmail API
        creds = authenticate_gmail(args.credentials_file, args.token_file)
        
        # Set up Gmail API watch if topic provided
        if args.topic:
            topic_name = validate_topic_name(args.topic, args.project_id)
            if topic_name:
                setup_gmail_watch(creds, topic_name)
        
        # Save token to Secret Manager if requested
        if args.save_to_secret_manager:
            save_to_secret_manager(args.project_id, args.token_file)
        
        print("\nAuthentication completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
