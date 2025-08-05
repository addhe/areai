# Troubleshooting Guide for Auto Reply Email System

This guide provides solutions for common issues that may arise when deploying, configuring, or running the Auto Reply Email system.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Authentication Problems](#authentication-problems)
3. [Email Processing Failures](#email-processing-failures)
4. [AI Response Generation Issues](#ai-response-generation-issues)
5. [Performance Problems](#performance-problems)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Common Error Codes](#common-error-codes)

## Deployment Issues

### Infrastructure Deployment Failures

#### Symptom: Terraform apply fails with permission errors

**Possible Causes:**
- Insufficient IAM permissions for the user or service account running Terraform
- Required APIs not enabled in the GCP project

**Solutions:**
1. Verify you have the following roles:
   - `roles/owner` or a combination of:
   - `roles/editor`
   - `roles/iam.serviceAccountAdmin`
   - `roles/secretmanager.admin`
   - `roles/cloudfunctions.admin`

2. Enable required APIs:
```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com \
  iam.googleapis.com
```

#### Symptom: Cloud Function deployment fails

**Possible Causes:**
- Missing dependencies in requirements.txt
- Errors in function code
- Quota limits exceeded

**Solutions:**
1. Check Cloud Function logs:
```bash
gcloud functions logs read auto-reply-email --limit 50
```

2. Verify requirements.txt includes all dependencies:
```
google-api-python-client>=2.0.0
google-auth>=2.0.0
google-auth-oauthlib>=0.4.6
google-cloud-aiplatform>=1.0.0
google-cloud-pubsub>=2.0.0
google-cloud-secretmanager>=2.0.0
requests>=2.25.0
python-dateutil>=2.8.0
```

3. Deploy with verbose logging:
```bash
gcloud functions deploy auto-reply-email \
  --runtime python310 \
  --trigger-topic email-notifications \
  --service-account auto-reply-email-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --verbosity=debug
```

### Resource Creation Issues

#### Symptom: "Resource already exists" errors

**Possible Causes:**
- Previous deployment attempt left resources in place
- Resource names conflict with existing resources

**Solutions:**
1. Check for existing resources:
```bash
gcloud pubsub topics list | grep email
gcloud functions list | grep auto-reply
gcloud secrets list | grep gmail
```

2. Delete conflicting resources:
```bash
gcloud pubsub topics delete email-notifications
gcloud secrets delete gmail-oauth-token
```

3. Use unique resource names in terraform.tfvars:
```
project_id      = "your-project-id"
pubsub_topic    = "email-notifications-prod"
function_name   = "auto-reply-email-prod"
```

## Authentication Problems

### OAuth Token Issues

#### Symptom: "Invalid credentials" or "Token expired" errors

**Possible Causes:**
- OAuth token expired
- Token doesn't have required scopes
- Token revoked or invalid

**Solutions:**
1. Re-run the OAuth authentication flow:
```bash
python scripts/gmail_auth.py
```

2. Verify token has required scopes:
```python
from google.oauth2.credentials import Credentials
import json

with open('token.json', 'r') as token_file:
    token_data = json.load(token_file)
    credentials = Credentials.from_authorized_user_info(token_data)
    print(f"Token valid: {not credentials.expired}")
    print(f"Scopes: {credentials.scopes}")
```

3. Check if token is properly stored in Secret Manager:
```bash
gcloud secrets versions access latest --secret=gmail-oauth-token
```

#### Symptom: "Access Not Configured" errors

**Possible Causes:**
- Gmail API not enabled
- Billing not enabled for the project

**Solutions:**
1. Enable the Gmail API:
```bash
gcloud services enable gmail.googleapis.com
```

2. Verify API is enabled:
```bash
gcloud services list --enabled | grep gmail
```

### Service Account Issues

#### Symptom: "Permission denied" errors in Cloud Function logs

**Possible Causes:**
- Service account missing required roles
- Service account not properly attached to Cloud Function

**Solutions:**
1. Verify service account has required roles:
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --format=json | jq '.bindings[] | select(.members[] | contains("auto-reply-email-sa"))'
```

2. Grant missing roles:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:auto-reply-email-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:auto-reply-email-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

3. Verify service account is attached to the Cloud Function:
```bash
gcloud functions describe auto-reply-email \
  --format="value(serviceAccountEmail)"
```

## Email Processing Failures

### Gmail Watch Issues

#### Symptom: Not receiving notifications when emails arrive

**Possible Causes:**
- Gmail watch not set up or expired
- Pub/Sub topic permissions incorrect
- Watch configured for wrong user

**Solutions:**
1. Check if watch is active:
```bash
python -c "
from cloud_function.utils.gmail import initialize_gmail_service, get_watch_status
from google.cloud import secretmanager
import os

client = secretmanager.SecretManagerServiceClient()
name = f'projects/{os.environ.get(\"GCP_PROJECT_ID\")}/secrets/gmail-oauth-token/versions/latest'
response = client.access_secret_version(request={'name': name})
token = response.payload.data.decode('UTF-8')

service = initialize_gmail_service(token)
status = get_watch_status(service)
print(status)
"
```

2. Renew Gmail watch:
```bash
python scripts/gmail_auth.py --watch-only
```

3. Verify Pub/Sub topic permissions:
```bash
gcloud pubsub topics get-iam-policy email-notifications
```

#### Symptom: Duplicate email processing

**Possible Causes:**
- Multiple history records for the same email
- Cloud Function timeout and retry

**Solutions:**
1. Implement deduplication in your Cloud Function:
```python
def pubsub_trigger(event, context):
    """Process Pub/Sub event."""
    # Extract message data
    message_data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    history_id = message_data.get('historyId')
    
    # Check if this history ID was recently processed
    from google.cloud import firestore
    db = firestore.Client()
    
    # Use history ID as a deduplication key
    doc_ref = db.collection('processed_history_ids').document(history_id)
    doc = doc_ref.get()
    
    if doc.exists:
        logging.info(f"History ID {history_id} already processed, skipping")
        return
    
    # Mark as processed with TTL of 1 hour
    import datetime
    doc_ref.set({
        'processed_at': datetime.datetime.now(),
        'expires_at': datetime.datetime.now() + datetime.timedelta(hours=1)
    })
    
    # Continue processing...
```

### Message Retrieval Issues

#### Symptom: "Message not found" errors

**Possible Causes:**
- Message deleted before processing
- Incorrect message ID
- Permissions issue

**Solutions:**
1. Add error handling for missing messages:
```python
def get_email_content(service, history_id):
    """Get email content from history ID."""
    try:
        # Get history details
        history = get_history(service, history_id)
        
        if not history or 'history' not in history:
            logging.error(f"No history found for ID {history_id}")
            return None
        
        # Find the message ID
        message_id = None
        for item in history['history']:
            if 'messagesAdded' in item:
                for message in item['messagesAdded']:
                    message_id = message['message']['id']
                    break
        
        if not message_id:
            logging.error(f"No message found in history {history_id}")
            return None
        
        # Get message content
        try:
            message = get_message(service, message_id)
            return extract_email_content(message)
        except Exception as e:
            logging.error(f"Error retrieving message {message_id}: {str(e)}")
            return None
            
    except Exception as e:
        logging.error(f"Error processing history {history_id}: {str(e)}")
        return None
```

2. Implement retry with backoff for transient errors:
```python
@retry(
    retry=retry_if_exception_type(HttpError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logging.getLogger(), logging.WARNING)
)
def get_message(service, message_id):
    """Get message with retry."""
    return service.users().messages().get(userId='me', id=message_id).execute()
```

## AI Response Generation Issues

### Vertex AI Errors

#### Symptom: "Failed to generate content" errors

**Possible Causes:**
- Vertex AI API not enabled
- Service account missing permissions
- Model not available in region
- Prompt exceeds token limits

**Solutions:**
1. Enable Vertex AI API:
```bash
gcloud services enable aiplatform.googleapis.com
```

2. Grant required permissions:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:auto-reply-email-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

3. Check if model is available in your region:
```bash
gcloud ai models list --region=us-central1 | grep gemini
```

4. Implement prompt truncation:
```python
def create_prompt(sender, subject, body, tone, customer_info=None):
    """Create prompt with length limits."""
    # Truncate email body if too long
    max_body_length = 1000
    if len(body) > max_body_length:
        body = body[:max_body_length] + "..."
    
    prompt = f"""
    You are a professional email assistant. Write a {tone} reply to this email:
    From: {sender}
    Subject: {subject}
    Content: {body}
    """
    
    if customer_info:
        # Include minimal customer info
        prompt += f"\nCustomer: {customer_info.get('name', 'Unknown')}, Status: {customer_info.get('status', 'Regular')}"
    
    prompt += "\nKeep your reply concise and directly address the inquiry."
    
    return prompt
```

#### Symptom: Low quality or irrelevant responses

**Possible Causes:**
- Insufficient prompt engineering
- Wrong model selection
- Missing context

**Solutions:**
1. Improve prompt structure (see prompt_engineering.md)

2. Try a different model:
```python
def initialize_vertex_ai(model_name="gemini-1.0-pro"):
    """Initialize Vertex AI with specified model."""
    aiplatform.init(project=os.environ.get("GCP_PROJECT_ID"), location=os.environ.get("GCP_REGION"))
    return model_name

def generate_ai_reply(sender, subject, body, tone, customer_info=None):
    """Generate AI reply with specified model."""
    model_name = initialize_vertex_ai()
    
    # Create prompt
    prompt = create_prompt(sender, subject, body, tone, customer_info)
    
    # Generate response
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error generating AI reply: {str(e)}")
        
        # Fall back to simpler model if primary fails
        try:
            fallback_model = GenerativeModel("text-bison@001")
            response = fallback_model.generate_content(prompt)
            return response.text
        except Exception as e2:
            logging.error(f"Fallback model also failed: {str(e2)}")
            return get_default_response(tone)
```

## Performance Problems

### Slow Response Times

#### Symptom: Responses taking longer than 15 seconds

**Possible Causes:**
- Insufficient Cloud Function memory
- Cold starts
- Slow API calls
- Complex email processing

**Solutions:**
1. Increase Cloud Function memory:
```bash
gcloud functions deploy auto-reply-email \
  --memory=512MB \
  --timeout=60s
```

2. Implement minimum instances to reduce cold starts:
```bash
gcloud functions deploy auto-reply-email \
  --min-instances=1
```

3. Optimize API calls with parallel processing:
```python
import asyncio
import aiohttp

async def process_email_async(email_address, history_id):
    """Process email with parallel API calls."""
    async with aiohttp.ClientSession() as session:
        # Create tasks for parallel execution
        email_task = asyncio.create_task(get_email_content_async(session, history_id))
        customer_task = asyncio.create_task(verify_customer_async(session, email_address))
        
        # Wait for both tasks to complete
        email_data, customer_info = await asyncio.gather(email_task, customer_task)
        
        # Generate AI reply (this still runs sequentially)
        reply = generate_ai_reply(
            email_data.get("from", ""),
            email_data.get("subject", ""),
            email_data.get("body", ""),
            "formal",
            customer_info
        )
        
        # Send reply
        success = await send_reply_async(session, email_data.get("from", ""), 
                                        email_data.get("subject", ""), reply)
        
        return success
```

4. Implement response caching for common queries:
```python
def get_cached_response(subject, body):
    """Get cached response if available."""
    # Create a hash of the email content
    import hashlib
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    # Check if response exists in cache
    from google.cloud import storage
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(f"{os.environ.get('GCP_PROJECT_ID')}-response-cache")
        blob = bucket.blob(f"responses/{content_hash}.json")
        
        if blob.exists():
            import json
            cached_data = json.loads(blob.download_as_string())
            if time.time() - cached_data["timestamp"] < 86400:  # 24 hours
                logging.info(f"Using cached response for hash {content_hash}")
                return cached_data["response"]
    except Exception as e:
        logging.warning(f"Cache check failed: {str(e)}")
    
    return None
```

### High Error Rates

#### Symptom: Many emails failing to receive responses

**Possible Causes:**
- Rate limiting by Gmail or Vertex AI
- Insufficient error handling
- Invalid email formats

**Solutions:**
1. Implement comprehensive error handling:
```python
def process_email_safely(email_address, history_id):
    """Process email with comprehensive error handling."""
    try:
        # Initialize services
        try:
            credentials = get_secret("gmail-oauth-token")
            service = initialize_gmail_service(credentials)
        except Exception as e:
            logging.error(f"Failed to initialize Gmail service: {str(e)}")
            return False
        
        # Get email content
        try:
            email_data = get_email_content(service, history_id)
            if not email_data:
                logging.error("Failed to retrieve email content")
                return False
        except Exception as e:
            logging.error(f"Error retrieving email: {str(e)}")
            return False
        
        # Process and send reply with individual error handling for each step
        try:
            customer_info = verify_customer(email_data.get("from", ""))
        except Exception as e:
            logging.warning(f"Customer verification failed: {str(e)}")
            customer_info = None  # Continue without customer info
        
        try:
            reply_text = generate_ai_reply(
                email_data.get("from", ""), 
                email_data.get("subject", ""), 
                email_data.get("body", ""),
                "formal", 
                customer_info
            )
            if not reply_text:
                logging.error("Failed to generate AI reply")
                reply_text = get_default_response("formal")
        except Exception as e:
            logging.error(f"AI generation failed: {str(e)}")
            reply_text = get_default_response("formal")
        
        try:
            success = send_reply(
                service, 
                email_data.get("from", ""), 
                email_data.get("subject", ""), 
                reply_text
            )
            return success
        except Exception as e:
            logging.error(f"Failed to send reply: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error in email processing: {str(e)}")
        return False
```

2. Implement rate limiting:
```python
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period  # in seconds
        self.calls = []
        self.lock = threading.Lock()
    
    def acquire(self):
        """Acquire permission to make an API call."""
        with self.lock:
            now = time.time()
            
            # Remove expired timestamps
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) >= self.max_calls:
                return False
            
            self.calls.append(now)
            return True

# Usage
gmail_limiter = RateLimiter(max_calls=100, period=60)  # 100 calls per minute

def rate_limited_api_call(limiter, func, *args, **kwargs):
    """Make a rate-limited API call."""
    if not limiter.acquire():
        time.sleep(1)  # Wait before retry
        return rate_limited_api_call(limiter, func, *args, **kwargs)
    
    return func(*args, **kwargs)
```

## Monitoring and Logging

### Missing or Insufficient Logs

#### Symptom: Unable to diagnose issues due to lack of logs

**Possible Causes:**
- Insufficient logging level
- Logs not being captured
- Log export not configured

**Solutions:**
1. Set appropriate logging level:
```python
import logging
import os

# Set log level from environment variable or default to INFO
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
```

2. Add structured logging:
```python
def log_structured_event(event_type, data):
    """Log structured event data."""
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.datetime.now().isoformat(),
        **data
    }
    logging.info(json.dumps(log_data))

# Usage
log_structured_event("email_received", {
    "history_id": history_id,
    "email_address": email_address
})

log_structured_event("ai_response_generated", {
    "from_email": sender,
    "subject": subject,
    "response_time": response_time,
    "token_count": token_count
})
```

3. Set up log export to BigQuery:
```bash
# Create BigQuery dataset
bq mk --dataset ${PROJECT_ID}:email_logs

# Create log sink
gcloud logging sinks create email-logs-sink \
  bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/email_logs \
  --log-filter='resource.type="cloud_function" AND resource.labels.function_name="auto-reply-email"'

# Get the service account for the sink
SERVICE_ACCOUNT=$(gcloud logging sinks describe email-logs-sink --format='value(writerIdentity)')

# Grant permissions
bq add-iam-policy-binding --member="${SERVICE_ACCOUNT}" --role="roles/bigquery.dataEditor" ${PROJECT_ID}:email_logs
```

### Alert Configuration Issues

#### Symptom: Not receiving alerts for system problems

**Possible Causes:**
- Alerts not properly configured
- Notification channels not set up
- Alert thresholds too high

**Solutions:**
1. Verify alert policies:
```bash
gcloud alpha monitoring policies list
```

2. Create or update alert policies:
```bash
python scripts/setup_monitoring.py --create-alerts --notification-email=your-email@example.com
```

3. Test alert notification channels:
```bash
# Get notification channel ID
CHANNEL_ID=$(gcloud alpha monitoring channels list --format='value(name)')

# Test notification channel
gcloud alpha monitoring channels verify $CHANNEL_ID
```

## Common Error Codes

### Gmail API Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| 400 | Bad Request | Check request format and parameters |
| 401 | Unauthorized | Refresh OAuth token |
| 403 | Forbidden | Check permissions and scopes |
| 404 | Not Found | Verify message/resource exists |
| 429 | Too Many Requests | Implement rate limiting and backoff |
| 500 | Server Error | Retry with exponential backoff |

### Vertex AI Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| INVALID_ARGUMENT | Invalid prompt format | Check prompt structure |
| PERMISSION_DENIED | Missing permissions | Grant aiplatform.user role |
| RESOURCE_EXHAUSTED | Quota exceeded | Request quota increase or implement rate limiting |
| FAILED_PRECONDITION | Model not ready | Check model availability in region |
| INTERNAL | Server error | Retry with exponential backoff |

### Cloud Function Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| 200-299 | Success | No action needed |
| 400 | Bad Request | Check Pub/Sub message format |
| 401 | Unauthorized | Check service account permissions |
| 408 | Timeout | Increase function timeout or optimize code |
| 429 | Too Many Requests | Scale function or implement rate limiting |
| 500-599 | Server Error | Check logs for details and fix code issues |

## Troubleshooting Decision Tree

Use this decision tree to diagnose and resolve issues:

1. **Is the system receiving email notifications?**
   - No → Check Gmail watch setup and Pub/Sub configuration
   - Yes → Continue to step 2

2. **Is the Cloud Function being triggered?**
   - No → Check Pub/Sub subscription and function trigger
   - Yes → Continue to step 3

3. **Is the function retrieving email content successfully?**
   - No → Check Gmail API authentication and permissions
   - Yes → Continue to step 4

4. **Is customer verification working?**
   - No → Check Customer API configuration or enable mock data
   - Yes → Continue to step 5

5. **Is AI response generation working?**
   - No → Check Vertex AI setup and prompt configuration
   - Yes → Continue to step 6

6. **Is the system sending replies successfully?**
   - No → Check Gmail API send permissions and rate limits
   - Yes → System is working correctly

For any persistent issues, check the Cloud Function logs for specific error messages and refer to the corresponding section in this guide.
