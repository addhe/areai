#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auto Reply Email with Vertex AI Gemini
Main Cloud Function entry point that processes Pub/Sub messages from Gmail API
"""

import base64
import json
import logging
import os
from typing import Dict, Any, Optional

from google.cloud import secretmanager

from utils.gmail import initialize_gmail_service, get_email_content, send_reply
from utils.vertex_ai import generate_ai_reply
from utils.customer_api import verify_customer

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
CUSTOMER_API_ENDPOINT = os.environ.get("CUSTOMER_API_ENDPOINT")
DEFAULT_TONE = "formal"


def get_secret(secret_id: str) -> str:
    """Retrieve secret from Secret Manager.
    
    Args:
        secret_id (str): ID of the secret to retrieve
        
    Returns:
        str: Secret value
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def validate_pubsub_message(data: Dict[str, Any]) -> bool:
    """Validate required fields in Pub/Sub message.
    
    Args:
        data (Dict[str, Any]): Message data from Pub/Sub
        
    Returns:
        bool: True if message is valid, False otherwise
    """
    required_fields = ["emailAddress", "historyId"]
    return all(field in data for field in required_fields)


def process_email(email_address: str, history_id: str) -> bool:
    """Process incoming email and generate AI reply.
    
    Args:
        email_address (str): Email address of the sender
        history_id (str): Gmail history ID
        
    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        # Initialize Gmail API service
        credentials = get_secret("gmail-oauth-token")
        service = initialize_gmail_service(credentials)
        
        # Get email content
        email_data = get_email_content(service, history_id)
        if not email_data:
            logger.error(f"Failed to retrieve email content for history ID: {history_id}")
            return False
        
        # Extract email details
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        sender = email_data.get("from", "")
        
        logger.info({
            "message": "Processing email",
            "sender": sender,
            "subject": subject,
            "history_id": history_id
        })
        
        # Verify customer (if applicable)
        customer_info = None
        try:
            customer_info = verify_customer(sender)
            logger.info(f"Customer verified: {sender}")
        except Exception as e:
            logger.warning(f"Customer verification failed: {str(e)}")
        
        # Generate AI reply
        tone = DEFAULT_TONE
        reply_text = generate_ai_reply(sender, subject, body, tone, customer_info)
        
        # Send reply
        success = send_reply(service, sender, subject, reply_text)
        
        logger.info({
            "message": "Email reply sent",
            "success": success,
            "sender": sender,
            "history_id": history_id
        })
        
        return success
        
    except Exception as e:
        logger.error({
            "message": "Failed to process email",
            "error": str(e),
            "email_address": email_address,
            "history_id": history_id
        })
        return False


def pubsub_trigger(event: Dict[str, Any], context) -> None:
    """Cloud Function entry point triggered by Pub/Sub.
    
    Args:
        event (Dict[str, Any]): Pub/Sub message
        context: Cloud Function context
    """
    try:
        # Decode Pub/Sub message
        if "data" not in event:
            logger.error("No data in Pub/Sub message")
            return
        
        pubsub_data = base64.b64decode(event["data"]).decode("utf-8")
        message_data = json.loads(pubsub_data)
        
        # Validate message format
        if not validate_pubsub_message(message_data):
            logger.error("Invalid Pub/Sub message format")
            return
        
        # Extract message details
        email_address = message_data["emailAddress"]
        history_id = message_data["historyId"]
        
        # Process email and send reply
        success = process_email(email_address, history_id)
        
        if not success:
            logger.error(f"Failed to process email for {email_address}")
        
    except Exception as e:
        logger.error(f"Error processing Pub/Sub message: {str(e)}")
        raise
