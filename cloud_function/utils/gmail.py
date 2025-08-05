#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail API utility functions for Auto Reply Email system
"""

import base64
import json
import logging
import time
import random
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, List

from google.api_core import exceptions as gcp_exceptions
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def initialize_gmail_service(credentials_json: str) -> Any:
    """Initialize Gmail API service client.
    
    Args:
        credentials_json (str): OAuth credentials JSON string
        
    Returns:
        Any: Gmail API service object
    """
    try:
        creds = Credentials.from_authorized_user_info(json.loads(credentials_json))
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail service: {str(e)}")
        raise


def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Execute function with exponential backoff retry.
    
    Args:
        func: Function to execute
        max_retries (int): Maximum number of retries
        base_delay (int): Base delay in seconds
        
    Returns:
        Any: Result of the function call
    """
    for attempt in range(max_retries):
        try:
            return func()
        except gcp_exceptions.ResourceExhausted:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Rate limited, retrying in {delay:.2f} seconds")
            time.sleep(delay)
        except HttpError as e:
            # Handle rate limit errors
            if e.resp.status in [429, 500, 503]:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"API error {e.resp.status}, retrying in {delay:.2f} seconds")
                time.sleep(delay)
            else:
                raise


def setup_gmail_watch(service, topic_name: str) -> Dict[str, Any]:
    """Set up Gmail API watch for new emails.
    
    Args:
        service: Gmail API service object
        topic_name (str): Pub/Sub topic name
        
    Returns:
        Dict[str, Any]: Watch response
    """
    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    
    return retry_with_backoff(
        lambda: service.users().watch(userId='me', body=request).execute()
    )


def get_message(service, message_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve email message using Gmail API.
    
    Args:
        service: Gmail API service object
        message_id (str): Message ID
        
    Returns:
        Optional[Dict[str, Any]]: Message data or None if not found
    """
    try:
        return retry_with_backoff(
            lambda: service.users().messages().get(userId='me', id=message_id).execute()
        )
    except gcp_exceptions.NotFound:
        logger.warning(f"Message {message_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {str(e)}")
        raise


def get_history(service, history_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve email history using Gmail API.
    
    Args:
        service: Gmail API service object
        history_id (str): History ID
        
    Returns:
        Optional[Dict[str, Any]]: History data or None if not found
    """
    try:
        return retry_with_backoff(
            lambda: service.users().history().list(
                userId='me', 
                startHistoryId=history_id,
                historyTypes=['messageAdded']
            ).execute()
        )
    except gcp_exceptions.NotFound:
        logger.warning(f"History {history_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error retrieving history {history_id}: {str(e)}")
        raise


def get_email_content(service, history_id: str) -> Optional[Dict[str, str]]:
    """Extract email content from history ID.
    
    Args:
        service: Gmail API service object
        history_id (str): History ID
        
    Returns:
        Optional[Dict[str, str]]: Email content with subject, body, and from fields
    """
    try:
        # Get history to find message ID
        history = get_history(service, history_id)
        if not history or 'history' not in history or not history['history']:
            logger.error(f"No history found for ID: {history_id}")
            return None
        
        # Get the most recent message ID from history
        message_added_events = []
        for item in history['history']:
            if 'messagesAdded' in item:
                message_added_events.extend(item['messagesAdded'])
        
        if not message_added_events:
            logger.error(f"No messages found in history: {history_id}")
            return None
        
        # Sort by internal date if available
        message_added_events.sort(
            key=lambda x: x.get('message', {}).get('internalDate', 0),
            reverse=True
        )
        
        message_id = message_added_events[0]['message']['id']
        
        # Get message details
        message = get_message(service, message_id)
        if not message:
            return None
        
        # Extract headers
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            # Multipart email
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body_bytes = base64.urlsafe_b64decode(part['body']['data'])
                        body = body_bytes.decode('utf-8')
                        break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            # Simple email
            body_bytes = base64.urlsafe_b64decode(message['payload']['body']['data'])
            body = body_bytes.decode('utf-8')
        
        return {
            'subject': subject,
            'body': body,
            'from': sender,
            'message_id': message_id
        }
        
    except Exception as e:
        logger.error(f"Error extracting email content: {str(e)}")
        return None


def create_message(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Create email message.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        Dict[str, Any]: Email message object
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
    
    return {
        'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()
    }


def send_reply(service, to: str, subject: str, body: str) -> bool:
    """Send email reply.
    
    Args:
        service: Gmail API service object
        to (str): Recipient email address
        subject (str): Original email subject
        body (str): Reply body
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        message = create_message(to, subject, body)
        retry_with_backoff(
            lambda: service.users().messages().send(userId='me', body=message).execute()
        )
        return True
    except Exception as e:
        logger.error(f"Error sending reply to {to}: {str(e)}")
        return False
