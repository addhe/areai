# Auto Reply Email System - API Documentation

This document provides detailed API documentation for the Auto Reply Email system, including utility modules, configuration options, and integration points.

## Table of Contents

1. [Gmail API Utilities](#gmail-api-utilities)
2. [Vertex AI Utilities](#vertex-ai-utilities)
3. [Customer API Utilities](#customer-api-utilities)
4. [Configuration Module](#configuration-module)
5. [Cloud Function Entry Point](#cloud-function-entry-point)
6. [Integration Points](#integration-points)

## Gmail API Utilities

Located in: `cloud_function/utils/gmail.py`

### `initialize_gmail_service(credentials_json)`

Initialize Gmail API service with OAuth credentials.

**Parameters:**
- `credentials_json` (str): JSON string containing OAuth credentials

**Returns:**
- `service`: Authenticated Gmail API service object

**Example:**
```python
service = initialize_gmail_service(credentials_json)
```

### `setup_watch(service, topic_name, label_ids=None)`

Set up Gmail API watch to send notifications to Pub/Sub.

**Parameters:**
- `service`: Authenticated Gmail API service
- `topic_name` (str): Pub/Sub topic name
- `label_ids` (list, optional): List of label IDs to watch

**Returns:**
- `dict`: Watch response with expiration time

**Example:**
```python
watch_response = setup_watch(service, "new-email")
```

### `get_email_content(service, history_id)`

Retrieve email content from history ID.

**Parameters:**
- `service`: Authenticated Gmail API service
- `history_id` (str): Gmail history ID

**Returns:**
- `dict`: Email content with keys: subject, body, from, to, date

**Example:**
```python
email_data = get_email_content(service, "12345")
```

### `create_message(to, subject, body, thread_id=None)`

Create email message object.

**Parameters:**
- `to` (str): Recipient email address
- `subject` (str): Email subject
- `body` (str): Email body
- `thread_id` (str, optional): Thread ID for reply

**Returns:**
- `dict`: Message object ready for sending

**Example:**
```python
message = create_message("user@example.com", "Re: Your Inquiry", "Thank you for your email...")
```

### `send_reply(service, to, subject, body, thread_id=None)`

Send reply email.

**Parameters:**
- `service`: Authenticated Gmail API service
- `to` (str): Recipient email address
- `subject` (str): Email subject
- `body` (str): Email body
- `thread_id` (str, optional): Thread ID for reply

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = send_reply(service, "user@example.com", "Re: Your Inquiry", "Thank you for your email...")
```

### `retry_with_backoff(func, max_retries=5, base_delay=1)`

Decorator for retry with exponential backoff.

**Parameters:**
- `func`: Function to retry
- `max_retries` (int): Maximum number of retry attempts
- `base_delay` (int): Base delay in seconds

**Returns:**
- Wrapped function with retry logic

**Example:**
```python
@retry_with_backoff(max_retries=3, base_delay=2)
def api_call():
    # Function that might fail temporarily
    pass
```

## Vertex AI Utilities

Located in: `cloud_function/utils/vertex_ai.py`

### `initialize_vertex_ai(project_id=None, location=None)`

Initialize Vertex AI client.

**Parameters:**
- `project_id` (str, optional): GCP project ID
- `location` (str, optional): GCP region

**Returns:**
- `client`: Vertex AI client

**Example:**
```python
client = initialize_vertex_ai("my-project", "us-central1")
```

### `create_prompt(sender, subject, body, tone, customer_info=None)`

Create AI prompt for email reply.

**Parameters:**
- `sender` (str): Email sender address
- `subject` (str): Email subject
- `body` (str): Email body
- `tone` (str): Desired tone (formal, friendly, etc.)
- `customer_info` (dict, optional): Customer data for personalization

**Returns:**
- `str`: Formatted prompt for Vertex AI

**Example:**
```python
prompt = create_prompt("user@example.com", "Product Inquiry", "I'm interested in...", "formal")
```

### `generate_ai_reply(sender, subject, body, tone="formal", customer_info=None)`

Generate AI reply using Vertex AI.

**Parameters:**
- `sender` (str): Email sender address
- `subject` (str): Email subject
- `body` (str): Email body
- `tone` (str, optional): Desired tone (formal, friendly, etc.)
- `customer_info` (dict, optional): Customer data for personalization

**Returns:**
- `str`: Generated reply text

**Example:**
```python
reply = generate_ai_reply("user@example.com", "Product Inquiry", "I'm interested in...", "formal")
```

### `fallback_reply(sender, subject)`

Generate fallback reply when AI generation fails.

**Parameters:**
- `sender` (str): Email sender address
- `subject` (str): Email subject

**Returns:**
- `str`: Fallback reply text

**Example:**
```python
reply = fallback_reply("user@example.com", "Product Inquiry")
```

## Customer API Utilities

Located in: `cloud_function/utils/customer_api.py`

### `verify_customer(email)`

Verify if email sender is a nasabah (customer) by querying the nasabah API.

**Parameters:**
- `email` (str): Email address to verify

**Returns:**
- `dict`: Customer data if verified, None otherwise with the following fields:
  - `name` (str): Customer name
  - `status` (str): Customer status ("aktif" or other)
  - `customer_id` (str): Customer ID
  - `account_type` (str): Account type ("premium" if saldo ≥ 10,000,000, otherwise "standard")
  - `saldo` (int): Account balance

**API Details:**
- **Endpoint**: `https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah?email={email}`
- **Method**: GET
- **Authentication**: API Key in `x-api-key` header
- **Environment Variables**:
  - `CUSTOMER_API_ENDPOINT`: API endpoint URL
  - `CUSTOMER_API_KEY`: API key for authentication

**Example:**
```python
customer_data = verify_customer("addhe.warman@outlook.co.id")
if customer_data:
    print(f"Customer: {customer_data['name']}")
    print(f"Account Type: {customer_data['account_type']}")
    print(f"Balance: Rp {customer_data['saldo']:,}")
```

### `get_mock_customer_data(email)`

Generate mock customer data for testing when API is unavailable.

**Parameters:**
- `email` (str): Email address

**Returns:**
- `dict`: Mock customer data with the same structure as the API response

**Example:**
```python
mock_data = get_mock_customer_data("addhe.warman@outlook.co.id")
```

**Available Mock Data:**
```python
{
    "client@example.com": {
        "name": "John Doe",
        "status": "active",
        "customer_id": "CUS123456",
        "account_type": "premium",
        "saldo": 15000000
    },
    "support@company.com": {
        "name": "Jane Smith",
        "status": "active",
        "customer_id": "CUS789012",
        "account_type": "standard",
        "saldo": 5000000
    },
    "addhe.warman@outlook.co.id": {
        "name": "Addhe Warman Putra",
        "status": "aktif",
        "customer_id": "7",
        "account_type": "premium",
        "saldo": 15000000
    }
}
```

## Configuration Module

Located in: `cloud_function/config.py`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | None |
| `GCP_REGION` | Google Cloud Region | `us-central1` |
| `CUSTOMER_API_ENDPOINT` | Nasabah API endpoint URL | `https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah` |
| `CUSTOMER_API_KEY` | Nasabah API authentication key | `b7f2e1c4-9a3d-4e8b-8c2a-7d5e6f1a2b3c` |
| `LOGGING_LEVEL` | Logging level | `INFO` |
| `ENABLE_CUSTOMER_VERIFICATION` | Enable customer verification | `True` |
| `VERTEX_AI_MODEL` | Vertex AI model name | `gemini-1.0-pro` |
| `MAX_RETRIES` | Maximum retry attempts | `5` |
| `BASE_DELAY` | Base delay for retries (seconds) | `1` |

### Constants

| Constant | Description | Value |
|----------|-------------|-------|
| `DEFAULT_TONE` | Default email tone | `formal` |
| `REPLY_PREFIX` | Email subject prefix | `Re: ` |
| `MAX_RESPONSE_TIME` | Maximum response time (seconds) | `15` |

## Cloud Function Entry Point

Located in: `cloud_function/main.py`

### `pubsub_trigger(event, context)`

Cloud Function entry point triggered by Pub/Sub.

**Parameters:**
- `event` (dict): Pub/Sub message event
- `context`: Cloud Function context

**Returns:**
- None

**Example Pub/Sub Message:**
```json
{
  "data": "BASE64_ENCODED_DATA",
  "attributes": {
    "key": "value"
  }
}
```

**Example Decoded Data:**
```json
{
  "emailAddress": "user@example.com",
  "historyId": "12345"
}
```

### `process_email(email_address, history_id)`

Process incoming email and generate AI reply.

**Parameters:**
- `email_address` (str): Email address of the sender
- `history_id` (str): Gmail history ID

**Returns:**
- `bool`: True if processing successful, False otherwise

**Example:**
```python
success = process_email("user@example.com", "12345")
```

### `get_secret(secret_id)`

Retrieve secret from Secret Manager.

**Parameters:**
- `secret_id` (str): ID of the secret to retrieve

**Returns:**
- `str`: Secret value

**Example:**
```python
token = get_secret("gmail-oauth-token")
```

## Integration Points

### Gmail API Integration

The system integrates with Gmail API using OAuth 2.0 authentication. Required scopes:

- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify emails (mark as read)
- `https://www.googleapis.com/auth/gmail.metadata` - Access email metadata

### Pub/Sub Integration

Gmail API notifications are sent to a Pub/Sub topic with the following format:

```json
{
  "message": {
    "data": "BASE64_ENCODED_DATA",
    "attributes": {}
  },
  "subscription": "projects/PROJECT_ID/subscriptions/email-subscriber"
}
```

Where the decoded data contains:

```json
{
  "emailAddress": "user@example.com",
  "historyId": "12345"
}
```

### Vertex AI Integration

The system uses Vertex AI Gemini model for generating email replies. The API is called with:

- Model: `gemini-1.0-pro`
- Temperature: `0.2` (for consistent, professional responses)
- Max output tokens: `1024`
- Top-k: `40`
- Top-p: `0.8`

### Customer API Integration

The system can integrate with an external Customer API to retrieve customer information. The API should return data in the following format:

```json
{
  "customer_id": "cust123",
  "name": "John Doe",
  "status": "active",
  "tier": "premium",
  "last_purchase": "2023-05-15",
  "preferences": {
    "communication": "email",
    "language": "en"
  }
}
```

### Secret Manager Integration

The system uses Secret Manager to store sensitive information:

- `gmail-oauth-token`: OAuth token for Gmail API
- `customer-api-key`: API key for Customer API (if applicable)

## Error Handling

All API calls include retry logic with exponential backoff:

1. Initial retry after 1 second
2. Second retry after 2 seconds
3. Third retry after 4 seconds
4. Fourth retry after 8 seconds
5. Fifth retry after 16 seconds

If all retries fail:
- Gmail API: Function will log error and exit
- Vertex AI: Function will use fallback reply
- Customer API: Function will proceed without customer data
