# Arsitektur Sistem Balas Email Otomatis

This document provides a comprehensive overview of the Auto Reply Email system architecture, components, and data flow.

## System Overview

The Auto Reply Email system is designed to automatically respond to incoming emails using AI-generated contextual replies. The system leverages Google Cloud Platform services to create a scalable, event-driven architecture that can process emails in near real-time.

Key features:
- Automatic email reply generation within 15 seconds
- Contextual AI responses using Vertex AI Gemini
- Customer data integration for personalized replies
- Robust error handling and retry mechanisms
- Comprehensive monitoring and alerting

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  Gmail API  │────▶│   Pub/Sub   │────▶│ Cloud Function  │────▶│  Vertex AI  │
│   (Watch)   │     │ (new-email) │     │(auto-reply-email)│     │  (Gemini)   │
└─────────────┘     └─────────────┘     └─────────────────┘     └─────────────┘
       ▲                                         │                     │
       │                                         │                     │
       │                                         ▼                     │
       │                               ┌─────────────────┐             │
       │                               │   Nasabah API   │             │
       │                               └─────────────────┘             │
       │                                         │                     │
       │                                         ▼                     │
       └───────────────────────────────────── Gmail API ◀──────────────┘
                                               (Send)
```

## Component Details

### 1. Gmail API

**Purpose:** Monitor inbox for new emails and send AI-generated replies.

**Key Functions:**
- `initialize_gmail_service()`: Set up authenticated Gmail API client
- `get_email_content()`: Retrieve email details from history ID
- `send_reply()`: Send AI-generated replies to email senders
- `setup_watch()`: Configure Gmail API to send notifications to Pub/Sub

**Authentication:** OAuth 2.0 with token stored in Google Secret Manager

### 2. Pub/Sub

**Purpose:** Event-driven messaging service that triggers Cloud Function when new emails arrive.

**Components:**
- Topic: `new-email`
- Subscription: `email-subscriber`

**Message Format:**
```json
{
  "emailAddress": "user@example.com",
  "historyId": "12345"
}
```

### 3. Cloud Function

**Purpose:** Process incoming email notifications and coordinate the auto-reply workflow.

**Entry Point:** `pubsub_trigger()`

**Workflow:**
1. Decode Pub/Sub message
2. Validate message format
3. Retrieve email content using Gmail API
4. Verify customer status (if applicable)
5. Generate AI reply using Vertex AI
6. Send reply using Gmail API
7. Log outcome

**Configuration:**
- Runtime: Python 3.11
- Memory: 256MB
- Timeout: 60s
- Service Account: `autoreply-sa@PROJECT_ID.iam.gserviceaccount.com`

### 4. Vertex AI (Gemini)

**Purpose:** Generate contextual, professional email replies based on email content.

**Key Functions:**
- `initialize_vertex_ai()`: Set up Vertex AI client
- `create_prompt()`: Generate AI prompt based on email content and customer data
- `generate_ai_reply()`: Call Vertex AI with retries and fallback mechanism

**Prompt Engineering:**
- Structured prompts with clear instructions
- Contextual information from original email
- Customer data integration for personalization
- Tone customization (formal, friendly, etc.)

### 5. Nasabah API

**Purpose:** Verify customer (nasabah) status and retrieve customer data for personalized replies.

**Key Functions:**
- `verify_customer()`: Check if email sender is a customer using nasabah API
- `get_mock_customer_data()`: Provide test data for development/testing and fallback

**API Details:**
- **Endpoint:** `https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah`
- **Method:** GET with email parameter
- **Authentication:** API Key in `x-api-key` header
- **Response Format:** JSON with customer details including name, status, ID, and saldo
- **Account Classification:** Premium for saldo ≥ 10,000,000, Standard otherwise

## Data Flow

1. **Email Notification:**
   - Gmail API watch detects new email
   - Notification sent to Pub/Sub topic

2. **Event Processing:**
   - Pub/Sub triggers Cloud Function
   - Function extracts email details from history ID

3. **Customer Verification:**
   - Email sender checked against Nasabah API
   - Customer data retrieved including name, status, account type, and saldo
   - Account type determined based on saldo threshold (Premium if ≥ 10,000,000)

4. **AI Reply Generation:**
   - Email content and customer data sent to Vertex AI
   - AI generates contextual reply based on prompt

5. **Reply Sending:**
   - Cloud Function sends reply via Gmail API
   - Success/failure logged for monitoring

## Error Handling

The system implements comprehensive error handling strategies:

1. **Retry Mechanisms:**
   - Exponential backoff for API calls
   - Configurable retry counts and delays

2. **Fallback Responses:**
   - Default reply templates when AI generation fails
   - Graceful degradation of service

3. **Logging and Monitoring:**
   - Structured logging for all operations
   - Alert policies for error rates and latency
   - Dashboard for system performance

## Security

1. **Authentication:**
   - OAuth 2.0 for Gmail API
   - Service account with least privilege
   - Secrets stored in Google Secret Manager

2. **Data Protection:**
   - No persistent storage of email content
   - In-memory processing only
   - Secure API communications

## Monitoring and Alerting

1. **Metrics:**
   - Email processing rate
   - Response time (95th percentile)
   - Error rate
   - Success rate

2. **Alert Policies:**
   - Error rate > 1%
   - Response time > 15 seconds
   - Function crashes
   - High invocation rate

3. **Dashboard:**
   - Real-time performance visualization
   - Historical trends
   - Error logs integration

## Deployment and Operations

1. **Infrastructure as Code:**
   - Terraform for GCP resource provisioning
   - Version-controlled configuration

2. **CI/CD Pipeline:**
   - Automated testing
   - Staged deployment
   - Validation checks

3. **Operational Procedures:**
   - Token refresh automation
   - Monitoring and incident response
   - Backup and recovery

## Performance Considerations

1. **Latency Optimization:**
   - Parallel API calls where possible
   - Memory optimization for Cloud Function
   - Efficient prompt design for AI

2. **Scalability:**
   - Event-driven architecture scales automatically
   - No state management required
   - Independent component scaling

3. **Quotas and Limits:**
   - Gmail API rate limits
   - Vertex AI quotas
   - Cloud Function concurrency

## Future Enhancements

1. **Multi-language Support:**
   - Language detection
   - Localized responses

2. **Advanced Analytics:**
   - Response effectiveness tracking
   - A/B testing of prompt strategies

3. **Integration Expansion:**
   - CRM system integration
   - Support ticket creation
   - Sentiment analysis

## Conclusion

The Auto Reply Email system provides a robust, scalable solution for automatically responding to emails with AI-generated contextual replies. The event-driven architecture ensures efficient processing, while comprehensive error handling and monitoring capabilities maintain system reliability.

## Privacy & Isolation (v2.1.0)

- **Per-email AI session**: Reply generation uses Vertex AI `GenerativeModel.start_chat(history=[])` per request to prevent cross-thread/customer memory.
- **Input minimization**: Quoted/forwarded history is removed from email body before prompt construction.
- **Output sanitization**: AI output is sanitized to redact non-+cs emails and long digit sequences that could be PII.
- **Secure reply routing**: Outbound `send_reply()` sets `From` and `Reply-To` to `addhe.warman+cs@gmail.com` to ensure replies return to the protected alias.
