#!/usr/bin/env python3
"""
Debug script to check specific email details
"""

import os
import json
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configuration
PROJECT_ID = "awanmasterpiece"
SECRET_NAME = "gmail-oauth-token"
MESSAGE_ID = "1987ffa089fb2ab9"  # From the logs

def get_credentials_from_secret_manager():
    """Get Gmail API credentials from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token_data = json.loads(response.payload.data.decode("UTF-8"))
        return Credentials.from_authorized_user_info(token_data)
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        return None

def debug_message(message_id):
    """Debug specific message details."""
    credentials = get_credentials_from_secret_manager()
    if not credentials:
        return
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get message details
        message = service.users().messages().get(userId='me', id=message_id).execute()
        
        print(f"🔍 Message ID: {message_id}")
        print(f"📧 Thread ID: {message.get('threadId')}")
        print(f"📅 Internal Date: {message.get('internalDate')}")
        print(f"🏷️  Label IDs: {message.get('labelIds', [])}")
        
        # Extract headers
        headers = message['payload'].get('headers', [])
        print("\n📋 Email Headers:")
        for header in headers:
            name = header['name']
            if name.lower() in ['from', 'to', 'subject', 'date']:
                print(f"   {name}: {header['value']}")
        
        # Check if it's in INBOX
        if 'INBOX' in message.get('labelIds', []):
            print("\n✅ Email is in INBOX")
        else:
            print("\n❌ Email is NOT in INBOX")
        
        # Check TO address specifically
        to_header = None
        for header in headers:
            if header['name'].lower() == 'to':
                to_header = header['value']
                break
        
        if to_header:
            print(f"\n🎯 TO Address Analysis:")
            print(f"   Full TO: {to_header}")
            if '+cs@gmail.com' in to_header.lower():
                print("   ✅ Contains +cs@gmail.com")
            else:
                print("   ❌ Does NOT contain +cs@gmail.com")
                print("   💡 This is why it wasn't processed!")
        
    except Exception as e:
        print(f"❌ Error debugging message: {e}")

def main():
    """Main debug function."""
    print("🔍 Gmail Auto-Reply Debug Tool")
    print("=" * 50)
    print(f"Debugging message: {MESSAGE_ID}")
    print("=" * 50)
    
    debug_message(MESSAGE_ID)
    
    print("\n" + "=" * 50)
    print("💡 Remember: System only processes emails sent to:")
    print("   squidgamecs2025@gmail.com")
    print("\n📧 If you want to test, send email to the +cs address!")

if __name__ == "__main__":
    main()
