#!/usr/bin/env python3
"""
Minimal Flask application to test endpoint logic
"""

import os
import json
import base64
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Add a flag for testing mode
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@app.route('/process', methods=['POST'])
def process_pubsub_push():
    """HTTP endpoint for Pub/Sub push messages."""
    logger.info("Received request to /process endpoint")
    
    # Log request headers for debugging
    headers = dict(request.headers)
    safe_headers = {k: v for k, v in headers.items() if 'auth' not in k.lower()}
    logger.info(f"Request headers: {safe_headers}")
    
    # Get request data
    envelope = request.get_json()
    logger.info(f"Request payload type: {type(envelope)}")
    logger.info(f"Request payload: {json.dumps(envelope, indent=2) if envelope else 'None'}")
    
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
        
        if not email_address or not history_id:
            logger.error(f"Missing email address or history ID in message data: {json_data}")
            return 'Missing email address or history ID', 400
            
        logger.info(f"Processing message for {email_address} with history ID {history_id}")
        
        # If in test mode, return success without processing
        if TEST_MODE:
            logger.info("Running in TEST_MODE, skipping credential retrieval and API calls")
            return jsonify({
                'status': 'success',
                'message': 'Test mode: Message received but not processed',
                'email_address': email_address,
                'history_id': history_id
            }), 200
            
        # In a real application, we would process the message here
        # For now, we'll just return success
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Error decoding or processing message data: {e}", exc_info=True)
        return f'Error processing message data: {str(e)}', 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
