#!/usr/bin/env python3
"""
Debug version of the auto-reply application
Simplified to isolate and fix issues
"""

import os
import json
import base64
import logging
import sys
import time
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask("debug_auto_reply_app")

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run."""
    logger.info("Health check endpoint called")
    return jsonify({
        'status': 'healthy',
        'python_version': sys.version,
        'timestamp': time.time()
    })

@app.route('/process', methods=['POST'])
def process_pubsub_push():
    """HTTP endpoint for Pub/Sub push messages."""
    logger.info("Received request to /process endpoint")
    try:
        # Log request headers for debugging
        headers = dict(request.headers)
        safe_headers = {k: v for k, v in headers.items() if 'auth' not in k.lower()}
        logger.info(f"Request headers: {safe_headers}")
        
        # Get request data
        try:
            envelope = request.get_json()
            logger.info(f"Request payload type: {type(envelope)}")
            # Log the actual payload for debugging
            logger.info(f"Request payload: {json.dumps(envelope, indent=2) if envelope else 'None'}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}", exc_info=True)
            return f'Error parsing JSON: {str(e)}', 400
            
        if not envelope:
            logger.error("No Pub/Sub message received")
            return 'No Pub/Sub message received', 400
            
        if not isinstance(envelope, dict) or 'message' not in envelope:
            logger.error(f"Invalid Pub/Sub message format: {envelope}")
            return 'Invalid Pub/Sub message format', 400
            
        message = envelope['message']
        logger.info("Extracted message from envelope")
        
        # Decode message data
        if 'data' not in message:
            logger.error("No data in Pub/Sub message")
            return 'No data in message', 400
            
        try:
            data = base64.b64decode(message['data']).decode('utf-8')
            logger.info(f"Decoded message data: {data}")
            
            # Parse the JSON data
            json_data = json.loads(data)
            logger.info(f"Parsed JSON data: {json_data}")
            
            # Extract email address and history ID
            email_address = json_data.get('emailAddress')
            history_id = json_data.get('historyId')
            
            logger.info(f"Extracted email address: {email_address}")
            logger.info(f"Extracted history ID: {history_id}")
            
            # In a real application, we would process the message here
            # For debugging, we'll just return success
            return jsonify({
                'status': 'success',
                'message': 'Message processed successfully',
                'email_address': email_address,
                'history_id': history_id
            })
            
        except Exception as e:
            logger.error(f"Error decoding or processing message data: {e}", exc_info=True)
            return f'Error processing message data: {str(e)}', 400
            
    except Exception as e:
        logger.error(f"Error processing Pub/Sub push: {e}", exc_info=True)
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    # This is used when running locally
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
