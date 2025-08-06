#!/usr/bin/env python3
"""
Script to check existing Gmail API watch status
"""

import os
import json
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import pubsub_v1

# Configuration
PROJECT_ID = "awanmasterpiece"
SECRET_NAME = "gmail-oauth-token"
TOPIC_NAME = "gmail-notifications"
SUBSCRIPTION_NAME = "gmail-notifications-sub"

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

def check_pubsub_topic():
    """Check if Pub/Sub topic exists."""
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
        
        try:
            topic = publisher.get_topic(request={"topic": topic_path})
            print(f"✅ Pub/Sub Topic exists: {topic.name}")
            return True
        except Exception:
            print(f"❌ Pub/Sub Topic does not exist: {topic_path}")
            return False
    except Exception as e:
        print(f"❌ Error checking Pub/Sub topic: {e}")
        return False

def check_pubsub_subscription():
    """Check if Pub/Sub subscription exists."""
    try:
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
        
        try:
            subscription = subscriber.get_subscription(request={"subscription": subscription_path})
            print(f"✅ Pub/Sub Subscription exists: {subscription.name}")
            print(f"   Push endpoint: {subscription.push_config.push_endpoint}")
            return True
        except Exception:
            print(f"❌ Pub/Sub Subscription does not exist: {subscription_path}")
            return False
    except Exception as e:
        print(f"❌ Error checking Pub/Sub subscription: {e}")
        return False

def check_gmail_watch():
    """Check Gmail watch status."""
    credentials = get_credentials_from_secret_manager()
    if not credentials:
        return False
    
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        # Try to get current watch status
        # Note: Gmail API doesn't have a direct way to check watch status
        # We'll try to get the profile which will work if credentials are valid
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail API connection successful")
        print(f"   Email: {profile.get('emailAddress')}")
        print(f"   Messages total: {profile.get('messagesTotal', 'N/A')}")
        print(f"   Threads total: {profile.get('threadsTotal', 'N/A')}")
        
        # Try to list labels to verify permissions
        labels = service.users().labels().list(userId='me').execute()
        print(f"✅ Gmail API permissions verified ({len(labels.get('labels', []))} labels found)")
        
        return True
    except Exception as e:
        print(f"❌ Error checking Gmail watch: {e}")
        return False

def main():
    """Main function to check Gmail auto-reply system status."""
    print("Checking Gmail Auto-Reply System Status...")
    print("=" * 50)
    
    # Check Pub/Sub components
    print("1. Checking Pub/Sub Topic...")
    topic_exists = check_pubsub_topic()
    
    print("\n2. Checking Pub/Sub Subscription...")
    subscription_exists = check_pubsub_subscription()
    
    print("\n3. Checking Gmail API connection...")
    gmail_ok = check_gmail_watch()
    
    print("\n" + "=" * 50)
    print("📊 Status Summary:")
    print(f"   Pub/Sub Topic: {'✅' if topic_exists else '❌'}")
    print(f"   Pub/Sub Subscription: {'✅' if subscription_exists else '❌'}")
    print(f"   Gmail API: {'✅' if gmail_ok else '❌'}")
    
    if topic_exists and subscription_exists and gmail_ok:
        print("\n🎉 All components are ready!")
        print("💡 If auto-reply is not working, you may need to setup Gmail watch.")
        print("   Run: python setup_gmail_watch.py")
    else:
        print("\n⚠️  Some components need setup:")
        if not topic_exists:
            print("   - Create Pub/Sub topic")
        if not subscription_exists:
            print("   - Create Pub/Sub subscription")
        if not gmail_ok:
            print("   - Fix Gmail API credentials")
        print("\n💡 Run: python setup_gmail_watch.py to setup missing components")

if __name__ == "__main__":
    main()
