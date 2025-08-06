#!/usr/bin/env python3
"""
Script to setup Gmail API watch for auto-reply system
This script will:
1. Create a Pub/Sub topic
2. Create a Pub/Sub subscription
3. Setup Gmail watch to send notifications to the topic
"""

import os
import json
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import PushConfig
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configuration
PROJECT_ID = "awanmasterpiece"
TOPIC_NAME = "gmail-notifications"
SUBSCRIPTION_NAME = "gmail-notifications-sub"
SECRET_NAME = "gmail-oauth-token"
PUSH_ENDPOINT = "https://auto-reply-email-361046956504.us-central1.run.app/process"

def get_credentials_from_secret_manager():
    """Get Gmail API credentials from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    token_data = json.loads(response.payload.data.decode("UTF-8"))
    return Credentials.from_authorized_user_info(token_data)

def create_pubsub_topic():
    """Create Pub/Sub topic for Gmail notifications."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
    
    try:
        topic = publisher.create_topic(request={"name": topic_path})
        print(f"Created topic: {topic.name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"Topic {topic_path} already exists")
        else:
            print(f"Error creating topic: {e}")
            raise

def create_pubsub_subscription():
    """Create Pub/Sub subscription with push endpoint."""
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = subscriber.topic_path(PROJECT_ID, TOPIC_NAME)
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
    
    push_config = PushConfig(push_endpoint=PUSH_ENDPOINT)
    
    try:
        subscription = subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "push_config": push_config,
            }
        )
        print(f"Created subscription: {subscription.name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"Subscription {subscription_path} already exists")
        else:
            print(f"Error creating subscription: {e}")
            raise

def setup_gmail_watch():
    """Setup Gmail watch to send notifications to Pub/Sub topic."""
    credentials = get_credentials_from_secret_manager()
    service = build('gmail', 'v1', credentials=credentials)
    
    topic_name = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"
    
    # Setup watch for INBOX only - we'll filter for +cs emails in the processing logic
    request_body = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    
    try:
        result = service.users().watch(userId='me', body=request_body).execute()
        print(f"Gmail watch setup successful!")
        print(f"History ID: {result.get('historyId')}")
        print(f"Expiration: {result.get('expiration')}")
        return result
    except Exception as e:
        print(f"Error setting up Gmail watch: {e}")
        raise

def main():
    """Main function to setup Gmail auto-reply system."""
    print("Setting up Gmail Auto-Reply System...")
    print("=" * 50)
    
    # Step 1: Create Pub/Sub topic
    print("1. Creating Pub/Sub topic...")
    create_pubsub_topic()
    
    # Step 2: Create Pub/Sub subscription
    print("2. Creating Pub/Sub subscription...")
    create_pubsub_subscription()
    
    # Step 3: Setup Gmail watch
    print("3. Setting up Gmail watch...")
    watch_result = setup_gmail_watch()
    
    print("\n" + "=" * 50)
    print("✅ Gmail Auto-Reply System Setup Complete!")
    print(f"📧 Target Email: addhe.warman+cs@gmail.com")
    print(f"🔔 Topic: projects/{PROJECT_ID}/topics/{TOPIC_NAME}")
    print(f"📡 Endpoint: {PUSH_ENDPOINT}")
    print(f"⏰ Watch expires: {watch_result.get('expiration')}")
    print("\n🔒 Security Features:")
    print("   - Only responds to emails sent to addhe.warman+cs@gmail.com")
    print("   - Only processes emails from last 24 hours")
    print("   - Filters out spam keywords")
    print("   - Prevents duplicate replies with auto-reply labels")
    print("\n🧪 To test, send an email to: addhe.warman+cs@gmail.com")

if __name__ == "__main__":
    main()
