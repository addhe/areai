# API Reference for Auto Reply Email System

This document provides a comprehensive reference for all APIs available in the Auto Reply Email system, including Cloud Functions, internal modules, and external integrations.

## Table of Contents

1. [Cloud Functions APIs](#cloud-functions-apis)
2. [Email Processing APIs](#email-processing-apis)
3. [AI Integration APIs](#ai-integration-apis)
4. [Customer Verification APIs](#customer-verification-apis)
5. [Management APIs](#management-apis)
6. [Monitoring APIs](#monitoring-apis)
7. [Webhook Integrations](#webhook-integrations)

## Cloud Functions APIs

### Email Processing Function

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/auto-reply-email`

**Method**: POST

**Description**: Main function triggered by Pub/Sub messages when new emails arrive.

**Request Format** (Pub/Sub message):

```json
{
  "message": {
    "data": "BASE64_ENCODED_DATA",
    "attributes": {
      "historyId": "12345678"
    }
  }
}
```

The base64-encoded data contains:

```json
{
  "emailAddress": "user@example.com",
  "historyId": "12345678"
}
```

**Response**:

```json
{
  "success": true,
  "messageId": "message-id-12345",
  "processingTime": 5.2
}
```

**Error Responses**:

| Status Code | Description | Response |
|-------------|-------------|----------|
| 400 | Bad Request | `{"error": "Invalid message format"}` |
| 401 | Unauthorized | `{"error": "Authentication failed"}` |
| 500 | Server Error | `{"error": "Failed to process email"}` |

### OAuth Token Refresh Function

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/refresh-oauth-token`

**Method**: POST

**Description**: Refreshes the OAuth token used for Gmail API access.

**Request Format**:

```json
{
  "secret_id": "gmail-oauth-token"
}
```

**Response**:

```json
{
  "success": true,
  "expiresAt": "2023-12-31T23:59:59Z"
}
```

### Gmail Watch Setup Function

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/setup-gmail-watch`

**Method**: POST

**Description**: Sets up or renews Gmail API watch for incoming emails.

**Request Format**:

```json
{
  "topicName": "projects/{project_id}/topics/email-notifications",
  "labelIds": ["INBOX"],
  "expirationSeconds": 604800
}
```

**Response**:

```json
{
  "success": true,
  "historyId": "12345678",
  "expiresAt": "2023-12-31T23:59:59Z"
}
```

## Email Processing APIs

### Gmail Service Module

**Module**: `cloud_function.utils.gmail`

#### `initialize_gmail_service(token)`

**Description**: Initializes the Gmail API service with the provided OAuth token.

**Parameters**:
- `token` (string): OAuth token JSON string

**Returns**: Authenticated Gmail service object

**Example**:

```python
from cloud_function.utils.gmail import initialize_gmail_service
from google.cloud import secretmanager

# Get token from Secret Manager
client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(request={"name": "projects/my-project/secrets/gmail-oauth-token/versions/latest"})
token = response.payload.data.decode("UTF-8")

# Initialize Gmail service
service = initialize_gmail_service(token)
```

#### `get_history(service, history_id)`

**Description**: Retrieves email history from the specified history ID.

**Parameters**:
- `service` (object): Gmail service object
- `history_id` (string): History ID to retrieve

**Returns**: Dictionary containing history data

**Example**:

```python
from cloud_function.utils.gmail import get_history

history = get_history(service, "12345678")
```

#### `get_message(service, message_id)`

**Description**: Retrieves a specific email message by ID.

**Parameters**:
- `service` (object): Gmail service object
- `message_id` (string): Message ID to retrieve

**Returns**: Dictionary containing message data

**Example**:

```python
from cloud_function.utils.gmail import get_message

message = get_message(service, "message-id-12345")
```

#### `extract_email_content(message)`

**Description**: Extracts relevant content from a Gmail message.

**Parameters**:
- `message` (dict): Gmail message object

**Returns**: Dictionary with extracted email data:
- `from` (string): Sender email
- `to` (string): Recipient email
- `subject` (string): Email subject
- `body` (string): Email body text
- `html` (string): Email HTML content (if available)
- `thread_id` (string): Email thread ID
- `message_id` (string): Email message ID
- `date` (string): Email date

**Example**:

```python
from cloud_function.utils.gmail import extract_email_content

email_data = extract_email_content(message)
print(f"From: {email_data['from']}")
print(f"Subject: {email_data['subject']}")
```

#### `send_reply(service, to, subject, body, thread_id=None)`

**Description**: Sends an email reply.

**Parameters**:
- `service` (object): Gmail service object
- `to` (string): Recipient email address
- `subject` (string): Email subject
- `body` (string): Email body text
- `thread_id` (string, optional): Thread ID to reply to

**Returns**: Dictionary with message ID if successful

**Example**:

```python
from cloud_function.utils.gmail import send_reply

response = send_reply(
    service,
    "recipient@example.com",
    "Re: Your inquiry",
    "Thank you for your message. Here is our response...",
    "thread-id-12345"
)
```

#### `setup_gmail_watch(service, topic_name)`

**Description**: Sets up Gmail API watch for notifications.

**Parameters**:
- `service` (object): Gmail service object
- `topic_name` (string): Pub/Sub topic name

**Returns**: Dictionary with watch details

**Example**:

```python
from cloud_function.utils.gmail import setup_gmail_watch

watch = setup_gmail_watch(
    service,
    "projects/my-project/topics/email-notifications"
)
```

## AI Integration APIs

### Vertex AI Module

**Module**: `cloud_function.utils.ai`

#### `initialize_vertex_ai(model_name="gemini-1.0-pro")`

**Description**: Initializes the Vertex AI client with the specified model.

**Parameters**:
- `model_name` (string, optional): AI model name to use

**Returns**: Model name string

**Example**:

```python
from cloud_function.utils.ai import initialize_vertex_ai

model_name = initialize_vertex_ai("gemini-1.0-pro")
```

#### `create_prompt(sender, subject, body, tone, customer_info=None)`

**Description**: Creates an AI prompt for email response generation.

**Parameters**:
- `sender` (string): Sender email address
- `subject` (string): Email subject
- `body` (string): Email body text
- `tone` (string): Desired response tone (formal, friendly, etc.)
- `customer_info` (dict, optional): Customer information

**Returns**: Formatted prompt string

**Example**:

```python
from cloud_function.utils.ai import create_prompt

prompt = create_prompt(
    "customer@example.com",
    "Product inquiry",
    "I'm interested in your enterprise solution. Can you provide more details?",
    "formal",
    {"name": "John Doe", "tier": "enterprise"}
)
```

#### `generate_ai_reply(sender, subject, body, tone, customer_info=None, model=None, max_tokens=800)`

**Description**: Generates an AI response to an email.

**Parameters**:
- `sender` (string): Sender email address
- `subject` (string): Email subject
- `body` (string): Email body text
- `tone` (string): Desired response tone
- `customer_info` (dict, optional): Customer information
- `model` (string, optional): AI model to use
- `max_tokens` (int, optional): Maximum tokens in response

**Returns**: Generated response text

**Example**:

```python
from cloud_function.utils.ai import generate_ai_reply

response = generate_ai_reply(
    "customer@example.com",
    "Product inquiry",
    "I'm interested in your enterprise solution. Can you provide more details?",
    "formal",
    {"name": "John Doe", "tier": "enterprise"},
    model="gemini-1.0-pro",
    max_tokens=800
)
```

#### `evaluate_response_quality(original_email, ai_response)`

**Description**: Evaluates the quality of an AI-generated response.

**Parameters**:
- `original_email` (dict): Original email content
- `ai_response` (string): Generated AI response

**Returns**: Dictionary with quality metrics:
- `relevance_score` (float): 0-1 score of response relevance
- `tone_match` (float): 0-1 score of tone appropriateness
- `completeness` (float): 0-1 score of response completeness
- `overall_score` (float): Combined quality score

**Example**:

```python
from cloud_function.utils.ai import evaluate_response_quality

metrics = evaluate_response_quality(
    {
        "from": "customer@example.com",
        "subject": "Product inquiry",
        "body": "I'm interested in your enterprise solution. Can you provide more details?"
    },
    "Thank you for your interest in our enterprise solution..."
)

print(f"Overall quality score: {metrics['overall_score']}")
```

## Customer Verification APIs

### Nasabah API Module

**Module**: `cloud_function.utils.customer_api`

#### `verify_customer(email_address)`

**Description**: Verifies if an email address belongs to a known nasabah (customer).

**Parameters**:
- `email_address` (string): Email address to verify

**Returns**: Dictionary with customer information if found, None otherwise

**API Endpoint**: `https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah?email={email}`

**API Authentication**: API Key in `x-api-key` header

**Response Format**:
```json
{
  "data": [
    {
      "created_at": "2025-08-05T12:21:55.840202",
      "email": "addhe.warman@outlook.co.id",
      "id": 7,
      "nama": "Addhe Warman Putra",
      "saldo": 15000000,
      "status": "aktif"
    }
  ]
}
```

**Converted Response Format** (for internal use):
```json
{
  "name": "Addhe Warman Putra",
  "status": "aktif",
  "customer_id": "7",
  "account_type": "premium",
  "saldo": 15000000
}
```

**Example**:

```python
from cloud_function.utils.customer_api import verify_customer

customer_info = verify_customer("addhe.warman@outlook.co.id")
if customer_info:
    print(f"Customer: {customer_info['name']}, Status: {customer_info['status']}")
    print(f"Saldo: Rp {customer_info['saldo']:,}")
    print(f"Account Type: {customer_info['account_type']}")
else:
    print("Unknown customer")
```

#### `get_customer_preferences(customer_id)`

**Description**: Retrieves preferences for a specific customer.

**Parameters**:
- `customer_id` (string): Customer ID

**Returns**: Dictionary with customer preferences

**Example**:

```python
from cloud_function.utils.customer import get_customer_preferences

preferences = get_customer_preferences("cust-12345")
print(f"Preferred response tone: {preferences['response_tone']}")
```

#### `update_customer_interaction(customer_id, interaction_data)`

**Description**: Records a customer interaction.

**Parameters**:
- `customer_id` (string): Customer ID
- `interaction_data` (dict): Interaction details

**Returns**: Boolean indicating success

**Example**:

```python
from cloud_function.utils.customer import update_customer_interaction

success = update_customer_interaction(
    "cust-12345",
    {
        "type": "email",
        "subject": "Product inquiry",
        "timestamp": "2023-12-15T14:30:00Z",
        "response_id": "resp-67890"
    }
)
```

## Management APIs

### Admin API

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/admin-api`

**Method**: Various (GET, POST, PUT, DELETE)

**Description**: Administrative API for managing the Auto Reply Email system.

#### Get System Status

**Path**: `/status`

**Method**: GET

**Description**: Retrieves the current system status.

**Response**:

```json
{
  "status": "healthy",
  "components": {
    "gmail_api": "operational",
    "vertex_ai": "operational",
    "pubsub": "operational"
  },
  "metrics": {
    "emails_processed_24h": 152,
    "avg_response_time": 4.8,
    "error_rate": 0.02
  }
}
```

#### Update Configuration

**Path**: `/config`

**Method**: PUT

**Description**: Updates system configuration.

**Request**:

```json
{
  "ai_model": "gemini-1.0-pro",
  "default_tone": "formal",
  "max_tokens": 800,
  "response_timeout": 12
}
```

**Response**:

```json
{
  "success": true,
  "updated": ["ai_model", "default_tone", "max_tokens", "response_timeout"]
}
```

#### List Recent Emails

**Path**: `/emails`

**Method**: GET

**Description**: Lists recently processed emails.

**Query Parameters**:
- `limit` (int, optional): Maximum number of emails to return (default: 10)
- `offset` (int, optional): Offset for pagination (default: 0)
- `status` (string, optional): Filter by status (success, error, all)

**Response**:

```json
{
  "emails": [
    {
      "id": "email-12345",
      "from": "customer@example.com",
      "subject": "Product inquiry",
      "received_at": "2023-12-15T14:30:00Z",
      "processed_at": "2023-12-15T14:30:05Z",
      "status": "success",
      "response_id": "resp-67890"
    },
    // More emails...
  ],
  "total": 152,
  "limit": 10,
  "offset": 0
}
```

#### Get Email Details

**Path**: `/emails/{email_id}`

**Method**: GET

**Description**: Retrieves details for a specific email.

**Response**:

```json
{
  "id": "email-12345",
  "from": "customer@example.com",
  "to": "support@yourcompany.com",
  "subject": "Product inquiry",
  "body": "I'm interested in your enterprise solution...",
  "received_at": "2023-12-15T14:30:00Z",
  "processed_at": "2023-12-15T14:30:05Z",
  "processing_time": 5.2,
  "status": "success",
  "response": {
    "id": "resp-67890",
    "body": "Thank you for your interest in our enterprise solution...",
    "ai_model": "gemini-1.0-pro",
    "tokens_used": 320,
    "quality_score": 0.92
  }
}
```

## Monitoring APIs

### Metrics API

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/metrics-api`

**Method**: GET

**Description**: API for retrieving system metrics.

#### Get Performance Metrics

**Path**: `/metrics/performance`

**Method**: GET

**Description**: Retrieves performance metrics.

**Query Parameters**:
- `period` (string, optional): Time period (1h, 24h, 7d, 30d)
- `resolution` (string, optional): Data resolution (minute, hour, day)

**Response**:

```json
{
  "period": "24h",
  "resolution": "hour",
  "metrics": {
    "response_time": [
      {"timestamp": "2023-12-15T00:00:00Z", "value": 4.8},
      {"timestamp": "2023-12-15T01:00:00Z", "value": 5.1},
      // More data points...
    ],
    "error_rate": [
      {"timestamp": "2023-12-15T00:00:00Z", "value": 0.02},
      {"timestamp": "2023-12-15T01:00:00Z", "value": 0.01},
      // More data points...
    ],
    "emails_processed": [
      {"timestamp": "2023-12-15T00:00:00Z", "value": 12},
      {"timestamp": "2023-12-15T01:00:00Z", "value": 8},
      // More data points...
    ]
  }
}
```

#### Get AI Metrics

**Path**: `/metrics/ai`

**Method**: GET

**Description**: Retrieves AI-specific metrics.

**Response**:

```json
{
  "period": "24h",
  "metrics": {
    "token_usage": {
      "total": 125000,
      "prompt": 45000,
      "completion": 80000
    },
    "quality_scores": {
      "average": 0.89,
      "distribution": {
        "excellent": 0.65,
        "good": 0.25,
        "fair": 0.08,
        "poor": 0.02
      }
    },
    "model_usage": {
      "gemini-1.0-pro": 0.85,
      "text-bison@001": 0.15
    }
  }
}
```

#### Get Cost Metrics

**Path**: `/metrics/cost`

**Method**: GET

**Description**: Retrieves cost-related metrics.

**Response**:

```json
{
  "period": "30d",
  "total_cost": 125.80,
  "breakdown": {
    "vertex_ai": 78.50,
    "cloud_functions": 32.20,
    "pubsub": 5.10,
    "secret_manager": 1.00,
    "other": 9.00
  },
  "daily_trend": [
    {"date": "2023-12-15", "cost": 4.20},
    {"date": "2023-12-14", "cost": 4.15},
    // More data points...
  ]
}
```

## Webhook Integrations

### Outgoing Webhooks

#### Email Processed Webhook

**Description**: Sent when an email is processed.

**Delivery**: POST to configured webhook URL

**Payload**:

```json
{
  "event_type": "email_processed",
  "timestamp": "2023-12-15T14:30:05Z",
  "data": {
    "email_id": "email-12345",
    "from": "customer@example.com",
    "subject": "Product inquiry",
    "processing_time": 5.2,
    "status": "success",
    "response_id": "resp-67890"
  }
}
```

#### Error Webhook

**Description**: Sent when an error occurs.

**Delivery**: POST to configured webhook URL

**Payload**:

```json
{
  "event_type": "error",
  "timestamp": "2023-12-15T14:30:05Z",
  "error": {
    "code": "AUTH_ERROR",
    "message": "Failed to authenticate with Gmail API",
    "context": {
      "email_id": "email-12345",
      "component": "gmail_service"
    }
  }
}
```

### Incoming Webhooks

#### Trigger Email Processing

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/webhook-trigger`

**Method**: POST

**Description**: Manually triggers email processing.

**Request**:

```json
{
  "email_address": "user@example.com",
  "message_id": "message-id-12345"
}
```

**Response**:

```json
{
  "success": true,
  "task_id": "task-67890",
  "status": "processing"
}
```

#### Update AI Configuration

**Endpoint**: `https://{region}-{project_id}.cloudfunctions.net/webhook-config`

**Method**: POST

**Description**: Updates AI configuration.

**Request**:

```json
{
  "api_key": "your-webhook-api-key",
  "config": {
    "model": "gemini-1.0-pro",
    "temperature": 0.7,
    "max_tokens": 800
  }
}
```

**Response**:

```json
{
  "success": true,
  "updated_at": "2023-12-15T14:30:05Z"
}
```

## Authentication

All API endpoints require authentication. The following authentication methods are supported:

### Service Account Authentication

For server-to-server communication, use a Google Cloud service account:

1. Create a service account with appropriate permissions
2. Generate a JSON key file
3. Include an Authorization header with a signed JWT token

Example:

```python
from google.oauth2 import service_account
import google.auth.transport.requests

# Load service account key
credentials = service_account.Credentials.from_service_account_file(
    'service-account-key.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

# Create authenticated request
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

headers = {
    'Authorization': f'Bearer {credentials.token}'
}

# Make API request
response = requests.get(
    'https://us-central1-my-project.cloudfunctions.net/metrics-api/metrics/performance',
    headers=headers
)
```

### API Key Authentication

For webhook integrations, use API key authentication:

1. Generate an API key in the Google Cloud Console
2. Include the API key in the request header or query parameter

Example:

```bash
curl -X POST \
  'https://us-central1-my-project.cloudfunctions.net/webhook-trigger?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"email_address": "user@example.com", "message_id": "message-id-12345"}'
```

## Rate Limits

The following rate limits apply to API endpoints:

| API | Rate Limit |
|-----|------------|
| Cloud Functions APIs | 60 requests per minute |
| Admin API | 300 requests per minute |
| Metrics API | 600 requests per minute |
| Webhooks | 120 requests per minute |

Exceeding these limits will result in a 429 Too Many Requests response.

## Error Handling

All APIs use standard HTTP status codes and return error details in the response body:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested email was not found",
    "details": {
      "email_id": "non-existent-id"
    }
  }
}
```

Common error codes:

| Error Code | Description |
|------------|-------------|
| AUTHENTICATION_ERROR | Authentication failed |
| PERMISSION_DENIED | Insufficient permissions |
| INVALID_ARGUMENT | Invalid request parameters |
| RESOURCE_NOT_FOUND | Requested resource not found |
| RATE_LIMIT_EXCEEDED | API rate limit exceeded |
| INTERNAL_ERROR | Internal server error |

## Conclusion

This API reference provides comprehensive documentation for all APIs available in the Auto Reply Email system. For implementation examples and best practices, refer to the other guides in the documentation directory.
