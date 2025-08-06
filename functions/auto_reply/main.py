"""
Auto Reply Email Cloud Function
Triggered by Pub/Sub notifications from Gmail API watch
"""

import base64
import json
import os
import time
import logging
import sys
from flask import Flask, request, jsonify
from google.cloud import secretmanager
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel
import requests
import config

# Try to import GenAI SDK (optional)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.info("GenAI SDK not available, will use Vertex AI only")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Print Python version for debugging
logger.info(f"Python version: {sys.version}")

# Initialize Flask app with explicit import name
app = Flask('auto_reply_app')

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

# Configuration
PROJECT_ID = os.environ.get('PROJECT_ID')
SECRET_NAME = os.environ.get('SECRET_NAME', 'gmail-oauth-token')
VERTEX_MODEL = os.environ.get('VERTEX_MODEL', 'gemini-2.5-flash-lite')

# Email security configuration
ALLOWED_EMAIL_ADDRESS = 'addhe.warman+cs@gmail.com'  # Only respond to emails sent to this address
MAX_EMAIL_AGE_HOURS = 24  # Only process emails from last 24 hours
ALLOWED_SENDERS = [  # Whitelist of allowed sender domains (optional)
    # Add trusted domains here, e.g., 'gmail.com', 'company.com'
    # Leave empty to allow all senders to +cs address
]
AUTO_REPLY_LABEL = 'Auto-Replied'

def is_email_allowed(email_data):
    """Check if email meets security criteria for auto-reply."""
    try:
        # Check if email was sent to the allowed address
        to_address = email_data.get('to', '').lower()
        if ALLOWED_EMAIL_ADDRESS.lower() not in to_address:
            logger.info(f"Email not sent to allowed address. To: {to_address}, Expected: {ALLOWED_EMAIL_ADDRESS}")
            return False, "Email not sent to allowed address"
        
        # Check sender domain if whitelist is configured
        if ALLOWED_SENDERS:
            from_address = email_data.get('from', '')
            sender_domain = from_address.split('@')[-1].lower() if '@' in from_address else ''
            if not any(domain.lower() in sender_domain for domain in ALLOWED_SENDERS):
                logger.info(f"Sender domain not in whitelist: {sender_domain}")
                return False, "Sender domain not allowed"
        
        # Check for spam indicators
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        spam_keywords = ['viagra', 'casino', 'lottery', 'winner', 'urgent', 'click here', 'free money']
        if any(keyword in subject or keyword in body for keyword in spam_keywords):
            logger.info("Email contains spam keywords")
            return False, "Email contains spam keywords"
        
        logger.info("Email passed security checks")
        return True, "Email allowed"
        
    except Exception as e:
        logger.error(f"Error checking email security: {e}")
        return False, "Security check failed"

def is_email_recent(message):
    """Check if email is recent (within MAX_EMAIL_AGE_HOURS)."""
    try:
        import time
        from datetime import datetime, timedelta
        
        # Get email timestamp
        internal_date = int(message.get('internalDate', 0)) / 1000  # Convert from milliseconds
        email_time = datetime.fromtimestamp(internal_date)
        
        # Check if email is within allowed time window
        cutoff_time = datetime.now() - timedelta(hours=MAX_EMAIL_AGE_HOURS)
        
        if email_time < cutoff_time:
            logger.info(f"Email too old: {email_time} (cutoff: {cutoff_time})")
            return False
        
        logger.info(f"Email is recent: {email_time}")
        return True
        
    except Exception as e:
        logger.error(f"Error checking email age: {e}")
        return False  # Err on the side of caution

def get_credentials_from_secret_manager():
    """Get OAuth credentials from Secret Manager."""
    logger.info(f"Getting credentials from Secret Manager: {SECRET_NAME} in project {PROJECT_ID}")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        token_data = json.loads(response.payload.data.decode("UTF-8"))
        logger.info("Successfully retrieved credentials from Secret Manager")
        return Credentials.from_authorized_user_info(token_data)
    except Exception as e:
        logger.error(f"Error accessing secret: {e}")
        raise

def get_message(service, msg_id):
    """Get a Gmail message by ID."""
    try:
        message = service.users().messages().get(
            userId='me', 
            id=msg_id, 
            format='full'
        ).execute()
        return message
    except Exception as e:
        print(f"Error getting message {msg_id}: {e}")
        return None

def extract_email_data(message):
    """Extract relevant data from a Gmail message."""
    headers = message['payload']['headers']
    
    # Extract headers
    data = {
        'id': message['id'],
        'threadId': message['threadId'],
        'subject': '',
        'from': '',
        'to': '',
        'body': '',
        'reply_to': ''
    }
    
    # Get header values
    for header in headers:
        name = header['name'].lower()
        if name == 'subject':
            data['subject'] = header['value']
        elif name == 'from':
            data['from'] = header['value']
        elif name == 'to':
            data['to'] = header['value']
        elif name == 'reply-to':
            data['reply_to'] = header['value']
    
    # If no reply-to, use from
    if not data['reply_to']:
        data['reply_to'] = data['from']
    
    # Extract body
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                data['body'] = body
                break
    elif 'body' in message['payload'] and 'data' in message['payload']['body']:
        body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        data['body'] = body
    
    return data

def has_auto_reply_label(service, msg_id):
    """Check if message already has auto-reply label."""
    try:
        # Get message to check labels
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        
        # Check if label exists
        if 'labelIds' in message and AUTO_REPLY_LABEL in message['labelIds']:
            return True
        
        # Get all labels to find the auto-reply label ID
        labels = service.users().labels().list(userId='me').execute()
        
        # Check if our label exists
        label_id = None
        for label in labels.get('labels', []):
            if label['name'] == AUTO_REPLY_LABEL:
                label_id = label['id']
                break
        
        # Create label if it doesn't exist
        if not label_id:
            label = service.users().labels().create(
                userId='me',
                body={'name': AUTO_REPLY_LABEL}
            ).execute()
            label_id = label['id']
        
        # Check if message has this label
        if 'labelIds' in message and label_id in message['labelIds']:
            return True
            
        return False
    except Exception as e:
        print(f"Error checking labels: {e}")
        return False  # Assume not replied to be safe

def add_auto_reply_label(service, msg_id):
    """Add auto-reply label to message to prevent duplicate replies."""
    try:
        # Get all labels to find the auto-reply label ID
        labels = service.users().labels().list(userId='me').execute()
        
        # Check if our label exists
        label_id = None
        for label in labels.get('labels', []):
            if label['name'] == AUTO_REPLY_LABEL:
                label_id = label['id']
                break
        
        # Create label if it doesn't exist
        if not label_id:
            label = service.users().labels().create(
                userId='me',
                body={'name': AUTO_REPLY_LABEL}
            ).execute()
            label_id = label['id']
            logger.info(f"Created auto-reply label: {label_id}")
        
        # Add label to message
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        
        logger.info(f"Added auto-reply label to message {msg_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding auto-reply label: {e}")
        return False

def check_is_nasabah(email):
    """Check if the sender is a known customer via API.
    
    Returns:
        tuple: (is_nasabah, customer_data)
            - is_nasabah (bool): True if email belongs to a customer, False otherwise
            - customer_data (dict): Customer data if available, None otherwise
    """
    logger.info(f"Checking customer status for: {email}")
    try:
        headers = {
            'x-api-key': config.NASABAH_API_KEY,
            'Accept': 'application/json'
        }
        params = {'email': email}
        response = requests.get(config.NASABAH_API_URL, headers=headers, params=params, timeout=5)

        # Coba parse respons JSON jika ada
        response_data = None
        try:
            if response.text and response.text.strip():
                response_data = response.json()
        except ValueError as e:
            logger.error(f"Error parsing JSON response: {e} - Raw response: {response.text}")

        # Status 200 dengan data yang valid
        if response.status_code == 200:
            # Periksa apakah respons memiliki data yang diharapkan
            if response_data and isinstance(response_data, dict):
                # Jika API mengembalikan indikator status nasabah spesifik
                if 'is_nasabah' in response_data:
                    is_nasabah = response_data['is_nasabah']
                    if is_nasabah:
                        logger.info(f"Customer confirmed for email: {email}")
                        return True, response_data
                    else:
                        logger.info(f"API explicitly confirmed non-customer status for email: {email}")
                        return False, None
                # Jika tidak ada indikator spesifik, anggap sukses = nasabah ditemukan
                else:
                    logger.info(f"Customer found for email: {email} (implied from successful response)")
                    return True, response_data
            else:
                logger.warning(f"API returned 200 but with unexpected data format for email: {email}")
                # Default ke False jika format data tidak sesuai harapan
                return False, None
                
        # Status 404 berarti nasabah tidak ditemukan
        elif response.status_code == 404:
            logger.info(f"Customer not found for email: {email}")
            return False, None
            
        # Status lain dianggap error
        else:
            logger.error(f"Error checking customer status: API returned status {response.status_code} - {response.text}")
            # Default ke False untuk error
            return False, None

    except Exception as e:
        logger.error(f"Error calling Nasabah API: {e}")
        return False, None # Default to not being a customer if API fails

def generate_ai_response(email_data, is_nasabah, customer_data=None):
    """Generate an AI response using GenAI SDK with Vertex AI backend.
    
    Args:
        email_data (dict): Email data including from, subject, body
        is_nasabah (bool): Whether the sender is a verified customer
        customer_data (dict, optional): Customer data from API including saldo info
    """
    try:
        logger.info("Initializing GenAI client with Vertex AI backend")
        
        # Create GenAI client with Vertex AI backend
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="us-central1",
        )
        
        # Ekstrak informasi saldo jika tersedia
        saldo_info = ""
        if is_nasabah and customer_data and isinstance(customer_data, dict):
            if 'saldo' in customer_data:
                saldo_info = f"\n- Saldo Anda: Rp {customer_data['saldo']}"
            elif 'balance' in customer_data:
                saldo_info = f"\n- Saldo Anda: Rp {customer_data['balance']}"
        
        # Buat prompt dalam Bahasa Indonesia
        prompt = f"""Anda adalah asisten email AI yang membantu. Buat balasan yang sopan dan profesional untuk email ini.

PENTING:
- Balas dalam Bahasa Indonesia.
- JANGAN menambahkan frasa pengantar seperti "Tentu, ini balasannya:" atau sejenisnya.
- Langsung mulai dengan "Kepada [nama]" atau sapaan yang sesuai.
- Jika ada pertanyaan tentang saldo, berikan informasi saldo yang sebenarnya, bukan placeholder "[Jumlah Saldo Anda]".

Dari: {email_data['from']}
Subjek: {email_data['subject']}
Pesan: {email_data['body']}

Konteks Tambahan:
- Status Pengirim: {'Nasabah Terverifikasi' if is_nasabah else 'Bukan Nasabah'}{saldo_info}

Balasan Anda harus:
- Mengakui email mereka
- Membantu dan profesional
- Ringkas (2-3 kalimat)
- Diakhiri dengan sopan

Balasan:"""
        
        logger.info(f"Using model: {VERTEX_MODEL}")
        
        # Create content
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ]
            )
        ]
        
        # Generate content config
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.8,
            max_output_tokens=256,
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )
        
        # Generate response
        logger.info("Sending request to Vertex AI via GenAI SDK")
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model=VERTEX_MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        response_text = response_text.strip()
        logger.info(f"Successfully generated AI response: {response_text[:100]}...")
        return response_text
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        # Return a fallback response in case of error
        return "Thank you for your email. I'm an automated assistant and I'm currently experiencing technical difficulties. A human will review your message as soon as possible."

def send_reply(service, email_data, response_text):
    """Send an auto-reply email."""
    try:
        # Create message
        message = MIMEMultipart()
        message['to'] = email_data['reply_to']
        message['subject'] = f"Re: {email_data['subject']}"
        message['In-Reply-To'] = email_data['id']
        message['References'] = email_data['id']
        
        # Add body
        message.attach(MIMEText(response_text))
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': encoded_message, 'threadId': email_data['threadId']}
        ).execute()
        
        # Add label to original message
        service.users().messages().modify(
            userId='me',
            id=email_data['id'],
            body={'addLabelIds': [AUTO_REPLY_LABEL]}
        ).execute()
        
        print(f"Auto-reply sent: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        print(f"Error sending reply: {e}")
        return None

def process_message(service, msg_id):
    """Process a single message with security filters."""
    try:
        # Get message
        message = get_message(service, msg_id)
        
        if not message:
            logger.warning(f"Could not retrieve message {msg_id}, skipping")
            return
        
        # Check if email is recent
        if not is_email_recent(message):
            logger.info(f"Skipping old email {msg_id}")
            return
        
        # Check if already replied
        if has_auto_reply_label(service, msg_id):
            logger.info(f"Message {msg_id} already has auto-reply label, skipping")
            return
        
        # Extract email data
        logger.info("Extracting email data from message")
        email_data = extract_email_data(message)
        logger.info(f"Extracted email from: {email_data.get('from', 'unknown')} to: {email_data.get('to', 'unknown')}")
        
        # Check if email meets security criteria
        is_allowed, reason = is_email_allowed(email_data)
        if not is_allowed:
            logger.info(f"Skipping email {msg_id}: {reason}")
            return
        
        logger.info(f"Processing allowed email from {email_data.get('from')} to {email_data.get('to')}")
        
        # Check if sender is a customer
        sender_email = email_data.get('from', '').split('<')[-1].split('>')[0]
        is_nasabah, customer_data = check_is_nasabah(sender_email)

        # Generate AI response with customer context
        logger.info("Generating AI response for email")
        response_text = generate_ai_response(email_data, is_nasabah, customer_data)
        
        # Send reply
        logger.info("Sending auto-reply email")
        send_reply(service, email_data, response_text)
        logger.info("Auto-reply sent successfully")
        
        # Add auto-reply label to prevent duplicate replies
        try:
            add_auto_reply_label(service, msg_id)
        except Exception as e:
            logger.warning(f"Could not add auto-reply label: {e}")
    except Exception as e:
        logger.error(f"Error processing message {msg_id}: {e}", exc_info=True)

def process_new_messages(service, history_id):
    """Process new messages based on history ID."""
    try:
        # Get new messages
        try:
            history_result = service.users().history().list(
                userId="me",
                startHistoryId=history_id
            ).execute()
            logger.info(f"History result: {history_result}")
        except HttpError as e:
            logger.error(f"HTTP Error getting history: {e.resp.status} - {e._get_reason()}")
            if e.resp.status == 404:
                logger.info("This error is expected when using dummy history IDs for testing")
            return
        except Exception as e:
            logger.error(f"Unexpected error getting history: {e}", exc_info=True)
            return

        # Process new messages
        if "history" in history_result:
            logger.info(f"Found {len(history_result['history'])} history records")
            for i, history_record in enumerate(history_result["history"]):
                logger.info(f"Processing history record {i+1}: {history_record}")
                
                # Check for messagesAdded
                if "messagesAdded" in history_record:
                    logger.info(f"Found {len(history_record['messagesAdded'])} messages added")
                    for message_added in history_record["messagesAdded"]:
                        message_id = message_added["message"]["id"]
                        logger.info(f"Processing added message: {message_id}")
                        process_message(service, message_id)
                
                # Check for messages (general)
                if "messages" in history_record:
                    logger.info(f"Found {len(history_record['messages'])} messages in history")
                    for message in history_record["messages"]:
                        message_id = message["id"]
                        logger.info(f"Processing message from history: {message_id}")
                        process_message(service, message_id)
                
                # Log if no messages found
                if "messagesAdded" not in history_record and "messages" not in history_record:
                    logger.info(f"No messages found in history record {i+1}")
        else:
            logger.info("No history records found")
            
        logger.info("Successfully processed new messages")
    except Exception as e:
        logger.error(f"Error processing messages: {e}", exc_info=True)

# Cloud Functions entry point removed in favor of Flask HTTP endpoint

TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

@app.route('/process', methods=['POST'])
def process_pubsub_push():
    """HTTP endpoint for Pub/Sub push messages."""
    logger.info("Received request to /process endpoint")
    
    # Log request headers for debugging
    try:
        headers = dict(request.headers)
        safe_headers = {k: v for k, v in headers.items() if 'auth' not in k.lower()}
        logger.info(f"Request headers: {safe_headers}")
    except Exception as e:
        logger.error(f"Error processing request headers: {e}", exc_info=True)
    
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
        
        # Get credentials from Secret Manager
        try:
            logger.info("Attempting to retrieve credentials from Secret Manager")
            credentials = get_credentials_from_secret_manager()
            logger.info("Successfully retrieved credentials from Secret Manager")
        except Exception as e:
            logger.error(f"Error getting credentials: {e}", exc_info=True)
            return f'Error getting credentials: {str(e)}', 500
            
        # Build Gmail API service
        try:
            logger.info("Building Gmail API service")
            service = build('gmail', 'v1', credentials=credentials)
            logger.info("Successfully built Gmail API service")
        except Exception as e:
            logger.error(f"Error building Gmail API service: {e}", exc_info=True)
            return f'Error building Gmail API service: {str(e)}', 500
            
        # Process new messages
        try:
            logger.info(f"Processing new messages with history ID {history_id}")
            process_new_messages(service, history_id)
            logger.info("Successfully processed new messages")
            return 'OK', 200
        except Exception as e:
            logger.error(f"Error processing new messages: {e}", exc_info=True)
            return f'Error processing new messages: {str(e)}', 500
            
    except Exception as e:
        logger.error(f"Error decoding or processing message data: {e}", exc_info=True)
        return f'Error processing message data: {str(e)}', 400

# Add a health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run."""
    logger.info("Health check endpoint called")
    return jsonify({
        'status': 'healthy',
        'python_version': sys.version,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    # This is used when running locally
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
