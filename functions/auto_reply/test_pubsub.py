#!/usr/bin/env python3
"""
Test script to simulate a Pub/Sub push notification to the auto-reply service
"""

import base64
import json
import requests
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_pubsub_message(history_id):
    """Create a simulated Pub/Sub message with the given history ID."""
    # Create the data payload that would be in the Pub/Sub message
    data = {
        "emailAddress": "user@example.com",
        "historyId": history_id
    }
    
    # Base64 encode the data as it would be in a real Pub/Sub message
    encoded_data = base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
    
    # Create the Pub/Sub message envelope
    message = {
        "message": {
            "data": encoded_data,
            "messageId": "test-message-id",
            "publishTime": "2023-01-01T00:00:00.000Z"
        },
        "subscription": "projects/test-project/subscriptions/test-subscription"
    }
    
    return message

def send_test_request(url, history_id):
    """Send a test request to the specified URL with the given history ID."""
    message = create_pubsub_message(history_id)
    logger.info(f"Sending test request to {url} with history_id: {history_id}")
    logger.info(f"Request payload: {json.dumps(message, indent=2)}")
    
    try:
        # Set a longer timeout and disable keep-alive to avoid connection issues
        response = requests.post(
            url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=30,  # 30 second timeout
            stream=False  # Don't use streaming
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        return response
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        logger.error("This could be due to the Flask server crashing when processing the request.")
        logger.error("Check the Flask server logs for more details.")
    except Exception as e:
        logger.error(f"Error sending request: {e}")
        logger.error("Exception type: " + str(type(e)))
        
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the auto-reply service with a simulated Pub/Sub message")
    parser.add_argument("--url", default="http://localhost:8080/process", help="URL of the auto-reply service")
    parser.add_argument("--history-id", required=True, help="Gmail history ID to use in the test")
    
    args = parser.parse_args()
    
    send_test_request(args.url, args.history_id)
