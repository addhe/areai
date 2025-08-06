#!/usr/bin/env python3
"""
Simple test script to verify Flask application functionality
"""

import requests
import json
import base64
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:9990/process", help="URL to send test request to")
args = parser.parse_args()

# Create test data
test_data = {
    "emailAddress": "user@example.com",
    "historyId": "12345678"
}

# Encode test data as base64
encoded_data = base64.b64encode(json.dumps(test_data).encode('utf-8')).decode('utf-8')

# Create Pub/Sub message envelope
message = {
    "message": {
        "data": encoded_data,
        "messageId": "test-message-id",
        "publishTime": "2023-01-01T00:00:00.000Z"
    },
    "subscription": "projects/test-project/subscriptions/test-subscription"
}

# Send request to Flask application
try:
    response = requests.post(
        args.url,
        json=message,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
