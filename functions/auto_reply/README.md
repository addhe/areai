# Gmail API Auto-Reply System with Vertex AI

This directory contains a sophisticated, AI-powered email auto-reply system designed to run on Google Cloud. It leverages the Gmail API, Pub/Sub for real-time notifications, and Vertex AI (specifically the Gemini model) to generate intelligent, context-aware responses to incoming emails.

## Architecture

The system is designed as a serverless application, intended for deployment on Google Cloud Run. The workflow is as follows:

1.  **Gmail Watch**: The Gmail API is configured to monitor a specific email account for new messages.
2.  **Pub/Sub Notification**: When a new email arrives, Gmail sends a notification to a designated Pub/Sub topic.
3.  **Cloud Run Trigger**: A Pub/Sub subscription triggers the Cloud Run service, which hosts the Flask application (`main.py`).
4.  **Email Processing**: The application receives the notification, fetches the new email content using the Gmail API, and performs several security checks (e.g., sender validation, spam filtering, age of email).
5.  **AI Response Generation**: If the email passes the checks, its content is sent to Vertex AI's Gemini model (`generate_ai_genai.py`) to generate a relevant reply.
6.  **Send Reply**: The generated response is sent back to the original sender via the Gmail API.

## Key Features

-   **AI-Powered Replies**: Uses Vertex AI Gemini for generating human-like email responses.
-   **Real-time Processing**: Leverages Gmail API push notifications via Pub/Sub for immediate responses.
-   **Secure & Filtered**: Includes security mechanisms to process only specific emails (e.g., based on recipient address like `+cs`), filter spam, and avoid reply loops.
-   **Serverless**: Built to run on Google Cloud Run for scalability and cost-efficiency.
-   **Comprehensive Tooling**: Includes scripts for setup, testing, and deployment.

## Directory Structure

Here's an overview of the key files in this directory:

-   `main.py`: The core Flask application that handles incoming Pub/Sub messages, processes emails, and orchestrates the reply logic.
-   `generate_ai_genai.py`: Contains the function to interact with the Vertex AI Gemini model for response generation.
-   `requirements.txt`: Lists all the Python dependencies required for the project.
-   `deploy.sh`: A shell script to automate the deployment process to Google Cloud Run.
-   `setup_gmail_watch.py`: A script to configure the Gmail API watch notification on the target email account.
-   `activate_gmail_watch.py` & `check_gmail_watch.py`: Helper scripts to manage the Gmail watch lifecycle.
-   `*test*.py`: A suite of test scripts for verifying different components of the system, from simple unit tests to comprehensive integration tests.

## Setup and Deployment

1.  **Prerequisites**: Ensure you have a Google Cloud Project with the Gmail API, Pub/Sub API, Vertex AI API, and Secret Manager API enabled.
2.  **Permissions**: Run `setup_permissions.py` to configure the necessary IAM roles for the service account.
3.  **Authentication**: Run `gmail_auth.py` (from the parent `scripts` directory) to generate the necessary OAuth2 credentials and store them in Secret Manager.
4.  **Gmail Watch**: Execute `setup_gmail_watch.py` to link your Gmail account to the Pub/Sub topic.
5.  **Deployment**: Run the `deploy.sh` script to build the container image and deploy the service to Google Cloud Run.

## Testing

The system includes various test scripts:
-   `simple_test.py`: A basic test to check if the deployed service endpoint is responsive.
-   `comprehensive_test.py`: Simulates a Pub/Sub message to test the entire processing flow.
-   `test_genai.py`: Specifically tests the AI response generation module.

Run these scripts to ensure all parts of the system are functioning correctly before and after deployment.

A secure, AI-powered Gmail auto-reply system deployed on Google Cloud Run. The system automatically generates and sends personalized responses to emails using Google's Gemini AI model.

## 🚀 Features

### Core Functionality
- **AI-Powered Responses**: Uses Google GenAI SDK with Vertex AI backend (Gemini 2.5 Flash Lite)
- **Real-time Processing**: Gmail watch API with Pub/Sub push notifications for instant email detection
- **Secure Authentication**: Gmail OAuth credentials stored in Google Cloud Secret Manager
- **Cloud Native**: Deployed on Google Cloud Run with auto-scaling

### Security & Filtering
- **Email Address Filtering**: Only responds to emails sent to `addhe.warman+cs@gmail.com`
- **Time-based Filtering**: Only processes emails from the last 24 hours
- **Spam Protection**: Built-in spam keyword filtering
- **Duplicate Prevention**: Adds Gmail labels to prevent multiple replies to the same email
- **Domain Whitelisting**: Optional sender domain validation

### Monitoring & Debugging
- **Comprehensive Logging**: Detailed logs for all operations and errors
- **Health Check Endpoint**: `/` endpoint for service monitoring
- **Debug Tools**: Multiple test scripts for validation and troubleshooting

## 📁 Project Structure

### Core Files
- `main.py` - Main Flask application with Pub/Sub processing and AI response generation
- `deploy.sh` - Cloud Run deployment script
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python runtime specification
- `Procfile` - Gunicorn configuration
- `gunicorn_config.py` - Server configuration

### Setup & Management Scripts
- `setup_gmail_watch.py` - Sets up Pub/Sub topic, subscription, and Gmail watch
- `setup_permissions.py` - Configures IAM permissions for Gmail API and Pub/Sub
- `activate_gmail_watch.py` - Activates Gmail watch notifications
- `debug_email.py` - Debug specific email messages by ID

### Testing Scripts
- `test_genai_vertex.py` - Test GenAI SDK with Vertex AI backend
- `test_vertex_ai_v2.py` - Test Vertex AI integration
- `test_direct.py` - Direct API testing
- `simple_test.py` - Basic endpoint testing
- `comprehensive_test.py` - Full system simulation

## 🔧 Configuration

### Environment Variables
- `PROJECT_ID` - Google Cloud project ID (`awanmasterpiece`)
- `SECRET_NAME` - Gmail OAuth token secret name (default: `gmail-oauth-token`)
- `VERTEX_MODEL` - AI model name (default: `gemini-2.5-flash-lite`)

### Security Settings (Internal)
- `ALLOWED_EMAIL_ADDRESS` - Target email address (`addhe.warman+cs@gmail.com`)
- `MAX_EMAIL_AGE_HOURS` - Email age limit (24 hours)
- `AUTO_REPLY_LABEL` - Gmail label for processed emails (`Auto-Replied`)

## 🚀 Deployment

### Prerequisites
1. Google Cloud project with billing enabled
2. Gmail API enabled
3. Vertex AI API enabled
4. Pub/Sub API enabled
5. Secret Manager API enabled
6. Cloud Run API enabled

### Setup Process
1. **Deploy the application**:
   ```bash
   ./deploy.sh
   ```

2. **Set up Pub/Sub and Gmail watch**:
   ```bash
   python3 setup_gmail_watch.py
   ```

3. **Configure permissions**:
   ```bash
   python3 setup_permissions.py
   ```

4. **Activate Gmail watch**:
   ```bash
   python3 activate_gmail_watch.py
   ```

## 🔐 Security & Permissions

### Service Account Roles
- `roles/secretmanager.secretAccessor` - Access Gmail OAuth credentials
- `roles/aiplatform.user` - Use Vertex AI models
- `roles/pubsub.subscriber` - Receive Pub/Sub messages

### Gmail API Service Account
- `roles/pubsub.publisher` - Publish Gmail notifications to Pub/Sub topic

### Security Features
- OAuth 2.0 authentication with Gmail API
- Secure credential storage in Secret Manager
- Email address validation and filtering
- Spam detection and prevention
- Rate limiting and error handling

## 🧪 Testing

### Manual Testing
Send an email to `addhe.warman+cs@gmail.com` with:
- **Subject**: "Test AI Auto-Reply"
- **Body**: "Hello, I need help with your services."

### Automated Testing
```bash
# Test GenAI integration
python3 test_genai_vertex.py

# Test specific email
python3 debug_email.py <message_id>

# Test endpoints
python3 simple_test.py
```

## 📊 Monitoring

### Logs
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email" --limit=20 --project=awanmasterpiece

# View error logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auto-reply-email AND severity>=ERROR" --limit=10 --project=awanmasterpiece
```

### Health Check
```bash
curl https://auto-reply-email-361046956504.us-central1.run.app/
```

## 🔄 System Flow

1. **Email Received** → Gmail detects new email
2. **Notification Sent** → Gmail watch sends Pub/Sub notification
3. **Processing Triggered** → Cloud Run receives Pub/Sub push
4. **Security Check** → Validates email meets criteria (address, age, spam)
5. **AI Generation** → GenAI SDK generates personalized response
6. **Reply Sent** → Gmail API sends auto-reply
7. **Label Added** → Marks email as processed to prevent duplicates

## 🛠️ Troubleshooting

### Common Issues
- **No auto-replies**: Check Gmail watch status and Pub/Sub permissions
- **Fallback responses**: Verify Vertex AI API access and model availability
- **Missing emails**: Ensure emails are sent to `+cs` address and within 24 hours
- **Permission errors**: Run `setup_permissions.py` to fix IAM bindings

### Debug Commands
```bash
# Check Gmail watch status
python3 activate_gmail_watch.py

# Debug specific email
python3 debug_email.py <message_id>

# Test AI generation
python3 test_genai_vertex.py
```

## 📈 Production Considerations

- **Rate Limiting**: Gmail API has quotas and rate limits
- **Cost Management**: Vertex AI charges per token generated
- **Monitoring**: Set up alerts for errors and unusual activity
- **Backup**: Consider fallback mechanisms for AI service outages
- **Scaling**: Cloud Run auto-scales based on traffic

## 🔗 Dependencies

- `google-api-python-client` - Gmail API client
- `google-cloud-pubsub` - Pub/Sub messaging
- `google-cloud-secret-manager` - Secure credential storage
- `google-cloud-aiplatform` - Vertex AI integration
- `google-genai` - GenAI SDK for AI generation
- `flask` - Web framework
- `gunicorn` - WSGI server

---

**Status**: ✅ Production Ready  
**Last Updated**: August 2025  
**Version**: 2.0 (GenAI SDK Integration)

## Setup

1. Create a Google Cloud project
2. Enable the Gmail API, Pub/Sub API, Secret Manager API, and Vertex AI API
3. Create OAuth credentials for the Gmail API
4. Store the credentials in Secret Manager
5. Create a Pub/Sub topic and subscription for Gmail notifications
6. Deploy the application to Cloud Run using the deployment script
