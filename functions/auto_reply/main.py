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
# Config is loaded from environment variables

# Try to import GenAI SDK (optional)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    # GenAI SDK not available; will use Vertex AI only

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
PRIMARY_FROM = os.environ.get('PRIMARY_FROM', '')  # Optional: primary account address to use for From
USE_PRIMARY_FROM = os.environ.get('USE_PRIMARY_FROM', 'false').lower() == 'true'

# Gmail API Watch configuration
WATCH_EXPIRY_DAYS = 7  # Gmail API watch expires after 7 days

# Email security configuration
ALLOWED_EMAIL_ADDRESS = 'addhe.warman+cs@gmail.com'  # Only respond to emails sent to this address
MAX_EMAIL_AGE_HOURS = 24  # Only process emails from last 24 hours
ALLOWED_SENDERS = [  # Whitelist of allowed sender domains (optional)
    # Add trusted domains here, e.g., 'gmail.com', 'company.com'
    # Leave empty to allow all senders to +cs address
]
AUTO_REPLY_LABEL = 'Auto-Replied'

# Privacy & safety flags
STRICT_PRIVACY = True  # Enforce strict prompt rules and output sanitization

def is_email_allowed(email_data):
    """Check if email meets security criteria for auto-reply."""
    try:
        # Check if email was sent to the allowed address
        to_address = email_data.get('to', '').lower()
        if ALLOWED_EMAIL_ADDRESS.lower() not in to_address:
            logger.info(f"Email not sent to allowed address. To: {to_address}, Expected: {ALLOWED_EMAIL_ADDRESS}")
            return False, "Email not sent to allowed address"
        
        # Check if the email is from our own system (prevent reply loops)
        from_address = email_data.get('from', '').lower()
        from_name = email_data.get('from', '').lower()
        
        # Extract name from email format "Name <email@example.com>"
        if '<' in from_name and '>' in from_name:
            from_name = from_name.split('<')[0].strip().lower()
        
        # Check if email address matches our system
        if ALLOWED_EMAIL_ADDRESS.lower() in from_address:
            logger.info(f"Preventing reply loop: Email is from our own system {from_address}")
            return False, "Email is from our own system"
            
        # Check if sender name contains our system name (case insensitive)
        system_name = ALLOWED_EMAIL_ADDRESS.split('@')[0].lower()
        if system_name in from_name:
            logger.info(f"Preventing reply loop: Email is likely from our system (name match) {from_name}")
            return False, "Email is likely from our system (name match)"
            
        # Check if the sender is sending to themselves (common in reply loops)
        to_address = email_data.get('to', '').lower()
        sender_email = from_address
        if '<' in from_address and '>' in from_address:
            sender_email = from_address.split('<')[1].split('>')[0].lower()
            
        if sender_email and to_address and sender_email in to_address:
            logger.info(f"Preventing reply loop: Sender is sending to themselves - {sender_email} to {to_address}")
            return False, "Email is a potential reply loop (sender to self)"
            
        # Check for common reply loop patterns in the subject
        subject = email_data.get('subject', '').lower()
        reply_indicators = ['re:', 'fw:', 'fwd:']
        reply_count = 0
        
        for indicator in reply_indicators:
            reply_count += subject.count(indicator)
            
        if reply_count >= 2:
            logger.info(f"Preventing reply loop: Multiple reply indicators in subject - {subject}")
            return False, "Email has multiple reply indicators in subject"
        
        # Check for auto-reply headers or indicators in subject/body
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        # Check for auto-reply headers
        auto_submitted = email_data.get('auto_submitted', '').lower()
        x_auto_response_suppress = email_data.get('x_auto_response_suppress', '').lower()
        precedence = email_data.get('precedence', '').lower()
        x_autoreply = email_data.get('x_autoreply', '').lower()
        x_autorespond = email_data.get('x_autorespond', '').lower()
        
        # Check for standard auto-reply headers
        if auto_submitted and auto_submitted != 'no':
            logger.info(f"Email has auto-submitted header: {auto_submitted}")
            return False, "Email is an automatic reply (auto-submitted header)"
            
        if x_auto_response_suppress:
            logger.info(f"Email has x-auto-response-suppress header: {x_auto_response_suppress}")
            return False, "Email is an automatic reply (x-auto-response-suppress header)"
            
        if precedence in ['bulk', 'auto_reply', 'junk']:
            logger.info(f"Email has precedence header indicating auto-reply: {precedence}")
            return False, "Email is an automatic reply (precedence header)"
            
        if x_autoreply or x_autorespond:
            logger.info("Email has explicit auto-reply header")
            return False, "Email is an automatic reply (explicit header)"
        
        # Common auto-reply indicators in subject/body
        auto_reply_indicators = [
            'auto-reply', 'automatic reply', 'auto reply', 'out of office', 
            'automated response', 'do not reply', 'noreply', 'no-reply',
            'mailer-daemon', 'mail delivery', 'delivery status', 'delivery failure',
            'undeliverable', 'returned mail'
        ]
        
        if any(indicator in subject.lower() or indicator in body.lower() for indicator in auto_reply_indicators):
            logger.info("Email appears to be an automatic reply based on content")
            return False, "Email is an automatic reply (content indicators)"
        
        # Check sender domain if whitelist is configured
        if ALLOWED_SENDERS:
            sender_domain = from_address.split('@')[-1].lower() if '@' in from_address else ''
            if not any(domain.lower() in sender_domain for domain in ALLOWED_SENDERS):
                logger.info(f"Sender domain not in whitelist: {sender_domain}")
                return False, "Sender domain not allowed"
        
        # Check for spam indicators
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
        # Capture headers that indicate auto-generated emails
        elif name == 'auto-submitted':
            data['auto_submitted'] = header['value']
        elif name == 'x-auto-response-suppress':
            data['x_auto_response_suppress'] = header['value']
        elif name == 'precedence':
            data['precedence'] = header['value']
        elif name == 'x-autoreply':
            data['x_autoreply'] = header['value']
        elif name == 'x-autorespond':
            data['x_autorespond'] = header['value']
    
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

def strip_quoted_text(body):
    """Remove quoted previous messages from an email body to avoid leaking prior context.
    Simple heuristics for common reply formats.
    """
    try:
        if not body:
            return body
        lines = body.splitlines()
        cleaned = []
        for line in lines:
            l = line.strip()
            # Skip typical quoted markers
            if l.startswith('>'):
                continue
            if l.lower().startswith('on ') and 'wrote:' in l.lower():
                break
            if '-------- Forwarded message --------' in l:
                break
            if l.startswith('From:') and '@' in l:
                break
            cleaned.append(line)
        # Join and trim excessive blank lines
        text = '\n'.join(cleaned).strip()
        # Keep only the first 1500 chars to minimize accidental context leakage
        return text[:1500]
    except Exception:
        return body

def sanitize_generated_text(text):
    """Redact potential PII artifacts such as emails and long digit sequences."""
    try:
        import re
        if not text:
            return text
        # Redact email addresses except our cs alias
        def _mask_email(m):
            email = m.group(0)
            if 'addhe.warman+cs@gmail.com' in email:
                return email
            return '[redacted-email]'
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", _mask_email, text)
        # Redact long digit sequences (8+)
        text = re.sub(r"(?<!\d)(\d{8,})(?!\d)", "[redacted-number]", text)
        # Collapse multiple spaces/newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception:
        return text
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

def normalize_email(email):
    """Normalize email address for consistent comparison.
    
    Args:
        email (str): Email address to normalize
        
    Returns:
        str: Normalized email address (lowercase, stripped)
    """
    if not email:
        return ""
    
    # Extract email from format like "Name <email@example.com>"
    if '<' in email and '>' in email:
        email = email.split('<')[1].split('>')[0]
    
    return email.lower().strip()

def check_is_nasabah(email):
    """Check if the sender is a known customer via API.
    
    Returns:
        tuple: (is_nasabah, customer_data)
            - is_nasabah (bool): True if email belongs to a customer, False otherwise
            - customer_data (dict): Customer data if available, None otherwise
    """
    # Normalize email before checking
    normalized_email = normalize_email(email)
    logger.info(f"Checking customer status for: {email} (normalized: {normalized_email})")
    
    # Return early if email is empty after normalization
    if not normalized_email:
        logger.warning("Empty email after normalization, cannot check customer status")
        return False, None
    try:
        headers = {
            'x-api-key': config.NASABAH_API_KEY,
            'Accept': 'application/json'
        }
        params = {'email': normalized_email}
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
                # Jika respons berisi array data, ambil item pertama
                if 'data' in response_data and isinstance(response_data['data'], list) and len(response_data['data']) > 0:
                    customer_data = response_data['data'][0]
                    # Periksa apakah email dalam data cocok dengan email yang dinormalisasi
                    if 'email' in customer_data:
                        api_email = normalize_email(customer_data['email'])
                        if api_email == normalized_email:
                            logger.info(f"Customer found in data array for email: {email}")
                            return True, response_data
                        else:
                            logger.warning(f"Email mismatch in data array: requested {normalized_email}, but API returned {api_email}")
                            return False, None
                    else:
                        logger.warning(f"Email field missing in customer data for: {email}")
                        return False, None
                # Jika API mengembalikan indikator status nasabah spesifik
                if 'is_nasabah' in response_data:
                    is_nasabah = response_data['is_nasabah']
                    if is_nasabah:
                        logger.info(f"Customer confirmed for email: {email}")
                        return True, response_data
                    else:
                        logger.info(f"API explicitly confirmed non-customer status for email: {email}")
                        return False, None
                # Jika tidak ada indikator spesifik, periksa apakah ada data nasabah yang valid
                elif 'email' in response_data:
                    # Periksa apakah email dalam respons cocok dengan email yang dinormalisasi
                    api_email = normalize_email(response_data['email'])
                    if api_email == normalized_email:
                        logger.info(f"Customer found for email: {email} (matched email in response)")
                        return True, response_data
                    else:
                        logger.warning(f"Email mismatch: requested {normalized_email}, but API returned {api_email}")
                        return False, None
                else:
                    logger.warning(f"API response lacks customer verification data for email: {email}")
                    return False, None
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
        logger.info("Initializing Vertex AI for per-email chat session")
        # Initialize Vertex AI explicitly (stateless per request)
        vertexai.init(project=PROJECT_ID, location="us-central1")
        
        # Ekstrak informasi saldo jika tersedia
        saldo_info = ""
        if is_nasabah and customer_data and isinstance(customer_data, dict):
            # Cek apakah data customer berada dalam array 'data'
            if 'data' in customer_data and isinstance(customer_data['data'], list) and len(customer_data['data']) > 0:
                customer_data = customer_data['data'][0]  # Ambil data nasabah pertama
            
            # Ekstrak dan format saldo dengan benar
            if 'saldo' in customer_data:
                saldo_value = customer_data['saldo']
                # Format saldo dengan pemisah ribuan
                formatted_saldo = "{:,}".format(int(saldo_value)).replace(',', '.')
                saldo_info = f"\n- Saldo Anda: Rp {formatted_saldo}"
                logger.info(f"Extracted saldo: {saldo_value}, formatted as: {formatted_saldo}")
            elif 'balance' in customer_data:
                saldo_value = customer_data['balance']
                # Format saldo dengan pemisah ribuan
                formatted_saldo = "{:,}".format(int(saldo_value)).replace(',', '.')
                saldo_info = f"\n- Saldo Anda: Rp {formatted_saldo}"
                logger.info(f"Extracted balance: {saldo_value}, formatted as: {formatted_saldo}")
        
        # Preprocess: strip quoted history to avoid cross-thread leakage
        body_for_model = strip_quoted_text(email_data.get('body', '')) if STRICT_PRIVACY else email_data.get('body', '')

        # Buat prompt dalam Bahasa Indonesia dengan guardrails ketat
        prompt = f"""Anda adalah asisten email AI yang membantu. Buat balasan yang sopan dan profesional untuk email ini.

PENTING (KEAMANAN & PRIVASI):
- Hanya gunakan informasi yang ada pada email saat ini dan konteks tambahan yang diberikan di bawah ini.
- Jangan gunakan memori/riwayat percakapan lain, data dari email lain, atau pengetahuan eksternal tentang pelanggan.
- Jangan menyebutkan data pribadi apa pun selain nama pengirim dan saldo yang diberikan (jika ada). Dilarang menyebut email/telepon/nomor akun.
- Jika email menyinggung "pertanyaan terakhir" atau histori namun tidak jelas, jawab secara umum atau minta klarifikasi; jangan menebak atau mengutip histori yang tidak ada di email saat ini.
- Jika bukan nasabah terverifikasi, JANGAN sebut nominal saldo.

Dari: {email_data['from']}
Subjek: {email_data['subject']}
Pesan (sudah dibersihkan dari kutipan histori): {body_for_model}

Konteks Tambahan:
- Status Pengirim: {'Nasabah Terverifikasi' if is_nasabah else 'Bukan Nasabah'}{saldo_info}

Balasan harus:
- Sopan dan profesional, ringkas (2-3 kalimat)
- Tidak menyertakan placeholder apa pun
- Tidak meminta info sensitif (PIN/OTP/kata sandi)
- Tidak menyertakan tanda tangan otomatis di luar format yang diminta

Format:
Kepada [Nama],
[Isi 2-3 kalimat]

Hormat kami,
[Nama Anda/Departemen Anda]
"""
        
        logger.info(f"Using model: {VERTEX_MODEL} with isolated chat session")
        # Start an isolated chat session per email without any prior history
        model = GenerativeModel(VERTEX_MODEL)
        chat = model.start_chat(history=[])

        # Generation parameters (kept modest)
        gen_kwargs = {
            "temperature": 0.7,
            "top_p": 0.8,
            "max_output_tokens": 256,
            "stream": True,
        }

        # Stream the response safely
        logger.info("Sending message to Vertex AI chat session (streaming)")
        response_text = ""
        try:
            for chunk in chat.send_message(prompt, **gen_kwargs):
                try:
                    if hasattr(chunk, 'text') and chunk.text:
                        response_text += chunk.text
                except Exception:
                    # be resilient to chunk types
                    pass
            response_text = response_text.strip()
            if STRICT_PRIVACY:
                response_text = sanitize_generated_text(response_text)
            logger.info(f"Successfully generated AI response: {response_text[:100]}...")
            return response_text
        except Exception as stream_err:
            logger.error(f"Vertex AI streaming error on model {VERTEX_MODEL}: {stream_err}", exc_info=True)

        # Fallback: try non-streaming on configured model, then alternate models
        fallback_models = [VERTEX_MODEL, 'gemini-1.5-flash', 'gemini-1.5-flash-002']
        for m in fallback_models:
            try:
                if m != VERTEX_MODEL:
                    logger.info(f"Trying fallback model: {m}")
                    model = GenerativeModel(m)
                    chat = model.start_chat(history=[])
                nonstream_kwargs = {k: v for k, v in gen_kwargs.items() if k != 'stream'}
                resp = chat.send_message(prompt, **nonstream_kwargs)
                # resp could be a single object with .text
                text = getattr(resp, 'text', '') or ''
                text = text.strip()
                if not text:
                    continue
                if STRICT_PRIVACY:
                    text = sanitize_generated_text(text)
                logger.info(f"Generated AI response via fallback {m}: {text[:100]}...")
                return text
            except Exception as e2:
                logger.error(f"Fallback generation failed on model {m}: {e2}")
                continue

    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        # Return a fallback response in case of error
        return "Thank you for your email. I'm an automated assistant and I'm currently experiencing technical difficulties. A human will review your message as soon as possible."

def send_reply(service, email_data, response_text):
    """Send an auto-reply email."""
    try:
        # Dedup: if thread already has our alias reply, skip sending to prevent duplicates
        try:
            thread = service.users().threads().get(
                userId='me', id=email_data['threadId'], format='metadata',
                metadataHeaders=['From']
            ).execute()
            for m in thread.get('messages', []):
                headers = m.get('payload', {}).get('headers', [])
                from_val = next((h.get('value') for h in headers if h.get('name') == 'From'), '')
                if 'addhe.warman+cs@gmail.com' in (from_val or ''):
                    logger.info("Detected existing reply from +cs alias in thread; skipping duplicate send.")
                    return None
        except Exception as dedup_err:
            logger.warning(f"Dedup check failed, proceeding to send: {dedup_err}")

        # Create message
        message = MIMEMultipart()
        message['to'] = email_data['reply_to']
        message['subject'] = f"Re: {email_data['subject']}"
        # Ensure replies from recipients go to the +cs alias to align with inbound protections
        from_addr = 'addhe.warman+cs@gmail.com'
        # If alias isn't verified yet, optionally send from primary while keeping Reply-To to alias
        if USE_PRIMARY_FROM and PRIMARY_FROM:
            logger.info(f"Using PRIMARY_FROM for send: {PRIMARY_FROM}; Reply-To remains alias")
            from_addr = PRIMARY_FROM
        else:
            logger.info("Using alias as From for send: addhe.warman+cs@gmail.com")
        message['From'] = from_addr  # Gmail requires verified send-as for non-primary
        message['Reply-To'] = 'addhe.warman+cs@gmail.com'
        message['In-Reply-To'] = email_data['id']
        message['References'] = email_data['id']
        
        # Add auto-reply headers to prevent reply loops
        message['Auto-Submitted'] = 'auto-replied'
        message['X-Auto-Response-Suppress'] = 'All'
        message['Precedence'] = 'auto_reply'
        message['X-AutoReply'] = 'yes'
        
        # Add body
        message.attach(MIMEText(response_text))
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        logger.info(
            f"Attempting Gmail send: to={email_data['reply_to']}, threadId={email_data['threadId']}, from={from_addr}"
        )
        
        # Send message (labeling happens only after successful send)
        try:
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': encoded_message, 'threadId': email_data['threadId']}
            ).execute()
        except HttpError as he:
            # Log detailed Gmail error and do NOT label the original message
            status = getattr(he, 'status_code', None) or getattr(he, 'resp', {}).status if hasattr(getattr(he, 'resp', None), 'status') else None
            try:
                err_body = he.content.decode('utf-8') if hasattr(he, 'content') and he.content else str(he)
            except Exception:
                err_body = str(he)
            logger.error(f"Gmail send HttpError status={status}, body={err_body}")
            return None
        except Exception as e:
            logger.error(f"Gmail send unexpected error: {e}", exc_info=True)
            return None
        
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
        
        # Add label to original message
        service.users().messages().modify(
            userId='me',
            id=email_data['id'],
            body={'addLabelIds': [label_id]}
        ).execute()
        
        logger.info(f"Auto-reply sent: {sent_message['id']}")
        return sent_message['id']
    except Exception as e:
        logger.error(f"Error sending reply: {e}", exc_info=True)
        return None

def process_message(service, msg_id):
    """Process a single message with security filters."""
    try:
        # Get message
        message = get_message(service, msg_id)
        
        if not message:
            logger.warning(f"Could not retrieve message {msg_id}, skipping")
            return
        
        # Extra safety: never react to sent/draft/spam/trash messages
        msg_labels = set(message.get('labelIds', []))
        if any(l in msg_labels for l in ['SENT', 'DRAFT', 'SPAM', 'TRASH']):
            logger.info(f"Skipping message {msg_id} due to labels {msg_labels}")
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
        found_added = False
        if "history" in history_result:
            logger.info(f"Found {len(history_result['history'])} history records")
            processed_ids = set()
            for i, history_record in enumerate(history_result["history"]):
                logger.info(f"Processing history record {i+1}: {history_record}")

                # Only act on messages explicitly added in this history event to avoid duplicates
                if "messagesAdded" in history_record:
                    found_added = True
                    logger.info(f"Found {len(history_record['messagesAdded'])} messages added")
                    for message_added in history_record["messagesAdded"]:
                        message_id = message_added["message"]["id"]

                        # Skip duplicates within the same delivery
                        if message_id in processed_ids:
                            logger.info(f"Skipping already processed message in this batch: {message_id}")
                            continue

                        # Fetch minimal metadata to decide eligibility by labels
                        try:
                            meta = service.users().messages().get(
                                userId='me', id=message_id, format='metadata',
                                metadataHeaders=['From', 'To', 'Subject']
                            ).execute()
                        except Exception as e:
                            logger.warning(f"Could not fetch metadata for {message_id}: {e}. Skipping.")
                            continue

                        labels = set(meta.get('labelIds', []))
                        # Process only real incoming unread messages in the inbox
                        if 'INBOX' not in labels or 'UNREAD' not in labels:
                            logger.info(f"Skipping message {message_id} due to labels {labels} (needs INBOX+UNREAD)")
                            continue
                        # Never react to our own sent items or other non-incoming categories
                        if any(l in labels for l in ['SENT', 'DRAFT', 'SPAM', 'TRASH']):
                            logger.info(f"Skipping non-incoming message {message_id} due to labels {labels}")
                            continue

                        processed_ids.add(message_id)
                        logger.info(f"Processing added incoming unread message: {message_id}")
                        process_message(service, message_id)

                # Log if no messages found we care about
                if "messagesAdded" not in history_record:
                    logger.info(f"No messagesAdded found in history record {i+1}")
        else:
            logger.info("No history records found")

        # Fallback: historyId off-by-one can cause empty messagesAdded; retry once with (history_id - 1)
        if not found_added:
            try:
                adjusted_id = str(int(history_id) - 1)
                logger.info(f"No messagesAdded found; retrying history.list with adjusted startHistoryId={adjusted_id}")
                history_result_2 = service.users().history().list(
                    userId='me', startHistoryId=adjusted_id
                ).execute()
                if "history" in history_result_2:
                    processed_ids = set()
                    for i, history_record in enumerate(history_result_2["history"]):
                        if "messagesAdded" in history_record:
                            for message_added in history_record["messagesAdded"]:
                                message_id = message_added["message"]["id"]
                                if message_id in processed_ids:
                                    continue
                                try:
                                    meta = service.users().messages().get(
                                        userId='me', id=message_id, format='metadata',
                                        metadataHeaders=['From', 'To', 'Subject']
                                    ).execute()
                                except Exception as e:
                                    logger.warning(f"Could not fetch metadata for {message_id}: {e}. Skipping.")
                                    continue
                                labels = set(meta.get('labelIds', []))
                                if 'INBOX' not in labels or 'UNREAD' not in labels:
                                    continue
                                if any(l in labels for l in ['SENT', 'DRAFT', 'SPAM', 'TRASH']):
                                    continue
                                processed_ids.add(message_id)
                                logger.info(f"[Fallback] Processing added incoming unread message: {message_id}")
                                process_message(service, message_id)
                else:
                    logger.info("[Fallback] No history records found on retry")
            except Exception as e:
                logger.warning(f"Fallback retry with adjusted historyId failed: {e}")

        # Final backfill: If still nothing processed, scan a small batch of recent INBOX+UNREAD
        # to avoid missing legit new mail when history is empty (e.g., first run, watch resets).
        if not found_added:
            try:
                logger.info("No messagesAdded after fallback; running backfill scan of recent INBOX+UNREAD (max 10)")
                recent_list = service.users().messages().list(
                    userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=10
                ).execute()
                ids = [m['id'] for m in recent_list.get('messages', [])]
                logger.info(f"Backfill found {len(ids)} candidate unread messages")
                processed_backfill = 0
                for mid in ids:
                    try:
                        meta = service.users().messages().get(
                            userId='me', id=mid, format='metadata',
                            metadataHeaders=['From', 'To', 'Subject']
                        ).execute()
                        labels = set(meta.get('labelIds', []))
                        if any(l in labels for l in ['SENT', 'DRAFT', 'SPAM', 'TRASH']):
                            continue
                        logger.info(f"[Backfill] Processing unread message: {mid}")
                        process_message(service, mid)
                        processed_backfill += 1
                    except Exception as e:
                        logger.warning(f"Backfill skip {mid} due to error: {e}")
                logger.info(f"Backfill processed {processed_backfill} messages")
            except Exception as e:
                logger.warning(f"Backfill scan failed: {e}")

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

# Add a Gmail API watch status check endpoint
@app.route('/check-watch-status', methods=['GET'])
def check_watch_status():
    """Endpoint to check Gmail API watch status."""
    logger.info("Received request to check Gmail API watch status")
    
    try:
        # Get credentials from Secret Manager
        logger.info("Retrieving credentials from Secret Manager")
        credentials = get_credentials_from_secret_manager()
        
        # Build Gmail API service
        logger.info("Building Gmail API service")
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get profile to check if watch is active
        profile = service.users().getProfile(userId='me').execute()
        history_id = profile.get('historyId')
        
        # Check if history ID exists
        if history_id:
            logger.info(f"Watch appears to be active. Current history ID: {history_id}")
            return jsonify({
                'status': 'success',
                'watchActive': True,
                'historyId': history_id
            }), 200
        else:
            logger.warning("Watch status could not be determined")
            return jsonify({
                'status': 'warning',
                'watchActive': False,
                'message': 'Watch status could not be determined'
            }), 200
            
    except Exception as e:
        logger.error(f"Error checking Gmail API watch status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'watchActive': False,
            'message': f'Error checking Gmail API watch status: {str(e)}'
        }), 500

# Add a Gmail API watch renewal endpoint
@app.route('/renew-watch', methods=['POST'])
def renew_watch():
    """Endpoint to renew Gmail API watch."""
    logger.info("Received request to renew Gmail API watch")
    
    try:
        # Get credentials from Secret Manager
        logger.info("Retrieving credentials from Secret Manager")
        credentials = get_credentials_from_secret_manager()
        
        # Build Gmail API service
        logger.info("Building Gmail API service")
        service = build('gmail', 'v1', credentials=credentials)
        
        # Set up watch
        logger.info("Setting up Gmail API watch")
        request_body = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{PROJECT_ID}/topics/new-email'
        }
        
        # Execute watch request
        response = service.users().watch(userId='me', body=request_body).execute()
        
        # Log success
        history_id = response.get('historyId')
        expiration = response.get('expiration')
        logger.info(f"Watch setup successful. History ID: {history_id}, Expiration: {expiration}")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Gmail API watch renewed successfully',
            'historyId': history_id,
            'expiration': expiration
        }), 200
        
    except Exception as e:
        logger.error(f"Error renewing Gmail API watch: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error renewing Gmail API watch: {str(e)}'
        }), 500

# Add a Pub/Sub test endpoint
@app.route('/test-pubsub', methods=['POST'])
def test_pubsub():
    """Endpoint to test Pub/Sub integration."""
    logger.info("Received request to test Pub/Sub integration")
    
    try:
        # Create a test message similar to what Gmail API watch would send
        test_data = {
            'emailAddress': ALLOWED_EMAIL_ADDRESS,
            'historyId': str(int(time.time())),  # Use current timestamp as dummy history ID
        }
        
        # Log the test data
        logger.info(f"Test data: {test_data}")
        
        # Get credentials from Secret Manager
        logger.info("Retrieving credentials from Secret Manager")
        credentials = get_credentials_from_secret_manager()
        
        # Build Gmail API service
        logger.info("Building Gmail API service")
        service = build('gmail', 'v1', credentials=credentials)
        
        # Process the test message
        logger.info(f"Processing test message with history ID {test_data['historyId']}")
        
        # Get recent messages from inbox
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=5
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.warning("No recent messages found in inbox")
            return jsonify({
                'status': 'warning',
                'message': 'No recent messages found in inbox to process'
            }), 200
        
        # Process the most recent message
        msg_id = messages[0]['id']
        logger.info(f"Processing most recent message: {msg_id}")
        process_message(service, msg_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Pub/Sub test successful, processed most recent message',
            'messageId': msg_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing Pub/Sub integration: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error testing Pub/Sub integration: {str(e)}'
        }), 500

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
