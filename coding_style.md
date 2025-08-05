# **Python Coding Style Guide**

**Project**: Auto Reply Email dengan AI (Vertex AI Gemini)  
**Document Version**: 1.0  
**Date**: 2025-08-05  
**Author**: Roo  

---
## **1. Overview**

This document defines the Python coding standards for the Auto Reply Email system. All Python code (Cloud Functions, scripts, utilities) must follow these conventions to ensure consistency, readability, and maintainability.

---
## **2. General Principles**

- Code should be **explicit** and **readable**
- Prefer **simple solutions** over complex ones
- Use **type hints** for all function signatures
- Follow **PEP 8** style guidelines
- Document **public functions** with docstrings

---
## **3. Naming Conventions**

### **3.1 Variables & Functions**
Use `snake_case` for variables and function names:
```python
# Good
email_subject = "Meeting Request"
customer_status = "verified"

def parse_email_content():
    pass

def generate_ai_reply(prompt: str) -> str:
    pass
```

### **3.2 Classes**
Use `PascalCase` for class names:
```python
# Good
class EmailProcessor:
    pass

class GmailAPIHandler:
    pass
```

### **3.3 Constants**
Use `UPPER_SNAKE_CASE` for constants:
```python
# Good
MAX_RETRIES = 3
DEFAULT_REPLY_TIMEOUT = 15
GCP_PROJECT_ID = "autoreply-project-123"
```

---
## **4. Code Structure**

### **4.1 File Organization**
```python
# Standard Cloud Function structure
import json
import logging
from typing import Dict, Any

# GCP service clients
from google.cloud import pubsub_v1
from google.cloud import aiplatform

# Constants
FUNCTION_NAME = "auto_reply_email"

# Helper functions
def validate_email_format(email: str) -> bool:
    """Check if email format is valid"""
    pass

# Main function
def pubsub_trigger(event: Dict[str, Any], context):
    """Entry point for Pub/Sub triggered Cloud Function"""
    pass
```

### **4.2 Import Statements**
- Group imports in order: standard library, third-party, local
- Use explicit imports rather than wildcards
```python
# Good
import json
import logging
from typing import Dict, List, Optional

from google.cloud import pubsub_v1
from google.cloud import aiplatform
from google.oauth2.credentials import Credentials

from .utils.gmail import get_message, send_reply
from .utils.vertex_ai import generate_reply_content
```

---
## **5. Logging Standards**

Use structured logging for monitoring and debugging:

```python
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def pubsub_trigger(event, context):
    """Entry point for Pub/Sub triggered Cloud Function"""
    try:
        # Process message
        message_data = json.loads(event['data'])
        logger.info({
            "message": "Processing email reply",
            "email_id": message_data.get("historyId"),
            "sender": message_data.get("emailAddress")
        })
    except Exception as e:
        logger.error({
            "message": "Failed to process email",
            "error": str(e),
            "event_id": context.event_id
        })
        raise
```

---
## **6. Error Handling**

### **6.1 Exception Patterns**
Always catch specific exceptions and log appropriately:
```python
from google.api_core import exceptions as gcp_exceptions

def get_message(message_id: str) -> Dict[str, Any]:
    """Retrieve email content using Gmail API"""
    try:
        message = gmail_service.users().messages().get(
            userId="me",
            id=message_id
        ).execute()
        return message
    except gcp_exceptions.NotFound:
        logger.warning(f"Message {message_id} not found")
        return {}
    except gcp_exceptions.PermissionDenied:
        logger.error(f"Insufficient permissions for message {message_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving message {message_id}: {str(e)}")
        raise
```

### **6.2 Retry Logic**
Implement exponential backoff for transient failures:
```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Execute function with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return func()
        except gcp_exceptions.ResourceExhausted:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Rate limited, retrying in {delay:.2f} seconds")
            time.sleep(delay)
```

---
## **7. Security Practices**

### **7.1 Credential Management**
Never hardcode credentials. Use Secret Manager:
```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """Retrieve secret from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# In main function
GMAIL_CREDENTIALS = get_secret("gmail-oauth-token")
CUSTOMER_API_ENDPOINT = get_secret("customer-api-endpoint")
```

### **7.2 Input Validation**
Validate all inputs before processing:
```python
def validate_pubsub_message(data: Dict[str, Any]) -> bool:
    """Validate required fields in Pub/Sub message"""
    required_fields = ["emailAddress", "historyId"]
    return all(field in data for field in required_fields)

# In main function
if not validate_pubsub_message(message_data):
    logger.error("Invalid Pub/Sub message format")
    raise ValueError("Missing required message fields")
```

---
## **8. GCP Integration Patterns**

### **8.1 Gmail API Handling**
Structure API calls with proper error handling:
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def initialize_gmail_service(credentials: str):
    """Initialize Gmail API service client"""
    creds = Credentials.from_authorized_user_info(json.loads(credentials))
    return build("gmail", "v1", credentials=creds)

def get_email_content(service, message_id: str) -> Dict[str, str]:
    """Extract subject and body from email"""
    message = service.users().messages().get(userId="me", id=message_id).execute()
    payload = message["payload"]
    
    # Extract subject
    subject = next(header["value"] for header in payload["headers"] 
                  if header["name"] == "Subject")
    
    # Extract body
    body = ""
    if "parts" in payload:
        body_part = next(part for part in payload["parts"] 
                        if part["mimeType"] == "text/plain")
        body = body_part["body"]["data"]
    else:
        body = payload["body"]["data"]
    
    return {"subject": subject, "body": body.decode("base64")}
```

### **8.2 Vertex AI Integration**
Use consistent prompt structure:
```python
from google.cloud import aiplatform

def generate_ai_reply(sender: str, subject: str, body: str, tone: str) -> str:
    """Generate reply content using Vertex AI Gemini"""
    prompt = f"""
    Anda adalah asisten email profesional.
    Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas.
    Gunakan gaya bahasa {tone}.
    
    Berikut detail email yang masuk:
    - Pengirim: {sender}
    - Subjek: {subject}
    - Isi email:
    {body}
    
    Balas email ini dengan nada {tone}. Jangan sertakan tanda tangan pribadi.
    """
    
    model = aiplatform.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    return response.text.strip()
```

---
## **9. Testing Conventions**

### **9.1 Unit Test Structure**
Follow pytest naming conventions:
```python
# test_gmail_utils.py
import pytest
from unittest.mock import Mock

from src.utils.gmail import get_email_content, validate_email_format

def test_get_email_content_success():
    """Test successful email content extraction"""
    mock_service = Mock()
    # Setup mock return value
    mock_service.users().messages().get().execute.return_value = SAMPLE_MESSAGE
    
    result = get_email_content(mock_service, "test_message_id")
    assert "subject" in result
    assert "body" in result
    assert len(result["body"]) > 0

def test_validate_email_format_valid():
    """Test valid email format validation"""
    valid_email = "client@example.com"
    assert validate_email_format(valid_email) == True
```

### **9.2 Integration Test Patterns**
Test end-to-end flows with mocked dependencies:
```python
# test_main_flow.py
import pytest
from unittest.mock import patch, Mock

def test_pubsub_trigger_full_flow():
    """Test complete Pub/Sub trigger flow"""
    with patch('src.main.initialize_gmail_service') as mock_gmail, \
         patch('src.main.generate_ai_reply') as mock_ai, \
         patch('src.main.send_reply') as mock_send:
        
        # Setup mocks
        mock_gmail.return_value = Mock()
        mock_ai.return_value = "Thank you for your email"
        mock_send.return_value = True
        
        # Trigger function
        pubsub_trigger(SAMPLE_PUBSUB_EVENT, Mock())
        
        # Verify calls
        mock_gmail.assert_called_once()
        mock_ai.assert_called_once()
        mock_send.assert_called_once()
```

---
## **10. Documentation Standards**

### **10.1 Docstrings**
Use Google-style docstrings for all functions:
```python
def process_email_reply(email_address: str, history_id: str, tone: str) -> bool:
    """Process incoming email and send AI-generated reply.
    
    Args:
        email_address (str): Email address of sender
        history_id (str): Gmail history ID for message tracking
        tone (str): Reply tone - either "formal" or "casual"
        
    Returns:
        bool: True if reply was sent successfully, False otherwise
        
    Raises:
        ValueError: If email format is invalid
        RuntimeError: If AI reply generation fails
    """
    pass
```

---
## **11. Performance Considerations**

### **11.1 Memory Optimization**
Minimize object creation in loops:
```python
# Good - reuse objects
email_parts = []
for part in message_payload["parts"]:
    if part["mimeType"] == "text/plain":
        email_parts.append(part["body"]["data"])

# Avoid creating unnecessary temporary objects
```

### **11.2 Resource Management**
Properly close connections and clean up resources:
```python
def pubsub_trigger(event, context):
    """Entry point that ensures cleanup of resources"""
    service = None
    try:
        credentials = get_secret("gmail-oauth-token")
        service = initialize_gmail_service(credentials)
        # Process email
        process_email_reply(service, event, context)
    finally:
        if service:
            service.close()  # If applicable
```

---
## **12. Code Review Checklist**

Before merging code, verify:
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] Error handling covers all GCP exception types
- [ ] No hardcoded credentials or secrets
- [ ] Logging is structured and meaningful
- [ ] Unit tests cover 80%+ of new code
- [ ] Follows naming conventions
- [ ] Imports are properly organized