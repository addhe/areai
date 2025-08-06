#!/usr/bin/env python3
"""
Direct test script to simulate Pub/Sub message and test auto-reply system.
"""

import json
import base64
import requests
import sys

def test_direct_message():
    """Test the auto-reply system with a simulated Pub/Sub message."""
    
    # Cloud Run service URL
    service_url = "https://auto-reply-email-361046956504.us-central1.run.app"
    
    # Create a test Pub/Sub message
    # This simulates what Gmail sends when a new email arrives
    test_message = {
        "emailAddress": "addhe.warman@gmail.com",
        "historyId": "23137900"  # Use a recent history ID
    }
    
    # Encode the message as base64 (as Pub/Sub does)
    message_data = base64.b64encode(json.dumps(test_message).encode()).decode()
    
    # Create the Pub/Sub push format
    pubsub_message = {
        "message": {
            "data": message_data,
            "messageId": "test-message-123",
            "publishTime": "2024-01-20T10:00:00.000Z"
        }
    }
    
    print(f"Testing auto-reply system at: {service_url}/process")
    print(f"Simulating message: {test_message}")
    
    try:
        # Send the test message to our service
        response = requests.post(
            f"{service_url}/process",
            json=pubsub_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            print("Check the logs to see detailed processing information:")
            print("gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email\" --limit=20 --project=awanmasterpiece")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending test message: {e}")

if __name__ == "__main__":
    test_direct_message()
