import requests
import json
import base64
import argparse

def test_pubsub_message(url, email_address, history_id):
    """
    Test the deployed service with a simulated Pub/Sub push message
    """
    # Create a simulated Pub/Sub message
    message_data = {
        "emailAddress": email_address,
        "historyId": history_id
    }
    
    # Encode the message data as base64
    encoded_data = base64.b64encode(json.dumps(message_data).encode('utf-8')).decode('utf-8')
    
    # Create the Pub/Sub push request payload
    payload = {
        "message": {
            "data": encoded_data,
            "messageId": "test-message-123",
            "publishTime": "2025-08-06T14:00:00Z"
        },
        "subscription": "projects/awanmasterpiece/subscriptions/test-subscription"
    }
    
    # Send the request to the service
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error sending request: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the deployed auto-reply service")
    parser.add_argument("--url", required=True, help="URL of the deployed service endpoint")
    parser.add_argument("--email", default="test@example.com", help="Email address for the test message")
    parser.add_argument("--history", default="12345678", help="History ID for the test message")
    
    args = parser.parse_args()
    
    print(f"Testing deployed service at: {args.url}")
    print(f"Using email address: {args.email}")
    print(f"Using history ID: {args.history}")
    print("-" * 50)
    
    test_pubsub_message(args.url, args.email, args.history)
