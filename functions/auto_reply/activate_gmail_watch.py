#!/usr/bin/env python3
"""
Simple script to activate Gmail watch
"""

import os
import json
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configuration
PROJECT_ID = "awanmasterpiece"
SECRET_NAME = "gmail-oauth-token"
TOPIC_NAME = "gmail-notifications"

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

def activate_gmail_watch():
    """Activate Gmail watch."""
    print("🔔 Activating Gmail Watch...")
    
    credentials = get_credentials_from_secret_manager()
    if not credentials:
        return False
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        topic_name = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"
        
        request_body = {
            'labelIds': ['INBOX'],
            'topicName': topic_name
        }
        
        result = service.users().watch(userId='me', body=request_body).execute()
        
        print("✅ Gmail watch activated successfully!")
        print(f"📧 Monitoring: squidgamecs2025@gmail.com")
        print(f"🔔 Topic: {topic_name}")
        print(f"📊 History ID: {result.get('historyId')}")
        print(f"⏰ Expires: {result.get('expiration')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error activating Gmail watch: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Gmail Auto-Reply System - Watch Activation")
    print("=" * 50)
    
    success = activate_gmail_watch()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup Complete!")
        print("\n📝 Next Steps:")
        print("1. Send a test email to: squidgamecs2025@gmail.com")
        print("2. Check logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email\" --limit=10 --project=awanmasterpiece")
        print("\n🔒 Security Features Active:")
        print("   ✅ Only responds to emails sent to squidgamecs2025@gmail.com")
        print("   ✅ Only processes emails from last 24 hours")
        print("   ✅ Filters out spam keywords")
        print("   ✅ Prevents duplicate replies")
    else:
        print("❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
