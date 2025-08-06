# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-08-06

### Added
-   Initial setup of the Gmail Auto-Reply system as a Flask application.
-   Integration with Google Cloud Run for serverless deployment (`deploy.sh`).
-   Core logic in `main.py` to handle Pub/Sub notifications from Gmail API.
-   AI-powered response generation using Vertex AI Gemini (`generate_ai_genai.py`).
-   Comprehensive security filters to prevent spam and reply loops.
-   A full suite of testing scripts (`simple_test.py`, `comprehensive_test.py`, `test_genai.py`) to ensure reliability.
-   Scripts for automating setup, including permissions (`setup_permissions.py`) and Gmail watch configuration (`setup_gmail_watch.py`).
-   OAuth2 authentication flow (`scripts/gmail_auth.py`) to securely handle user credentials with Google Secret Manager.

### Changed
-   Refactored codebase for better modularity and readability.
-   Switched from basic AI models to Gemini for higher quality responses.

### Fixed
-   Resolved various linting errors and improved code quality.
-   Addressed initial authentication issues with Gmail API (`redirect_uri_mismatch`).

All notable changes to the Gmail API Auto-Reply System are documented in this file.

## [2.0.0] - 2025-08-06

### 🚀 Major Features Added
- **GenAI SDK Integration**: Migrated from direct Vertex AI calls to Google GenAI SDK with Vertex AI backend
- **Enhanced Security Filtering**: Added comprehensive email filtering system
- **Real-time Processing**: Implemented Gmail watch API with Pub/Sub push notifications
- **Comprehensive Logging**: Added detailed logging throughout the system

### 🔒 Security Enhancements
- **Email Address Filtering**: Only responds to emails sent to `addhe.warman+cs@gmail.com`
- **Time-based Filtering**: Only processes emails from the last 24 hours
- **Spam Protection**: Built-in spam keyword filtering
- **Duplicate Prevention**: Adds Gmail labels to prevent multiple replies
- **Domain Whitelisting**: Optional sender domain validation

### 🛠️ Technical Improvements
- **AI Model Upgrade**: Updated to use `gemini-2.5-flash-lite` model
- **Error Handling**: Improved error handling with fallback responses
- **Authentication**: Secure OAuth credential storage in Secret Manager
- **Cloud Native**: Optimized for Google Cloud Run deployment

### 📁 New Files Added
- `setup_gmail_watch.py` - Pub/Sub and Gmail watch setup
- `setup_permissions.py` - IAM permissions configuration
- `activate_gmail_watch.py` - Gmail watch activation
- `debug_email.py` - Email debugging utility
- `test_genai_vertex.py` - GenAI SDK testing
- `test_vertex_ai_v2.py` - Vertex AI integration testing
- `test_direct.py` - Direct API testing
- `generate_ai_genai.py` - GenAI SDK implementation
- `list_models.py` - Available models checker

### 🔧 Configuration Changes
- **Environment Variables**: 
  - `VERTEX_MODEL` default changed to `gemini-2.5-flash-lite`
  - Added internal security configuration variables
- **Dependencies**: Added `google-genai>=1.28.0` to requirements.txt
- **Model Configuration**: Updated AI generation parameters for better responses

### 🐛 Bug Fixes
- Fixed Vertex AI model access issues
- Resolved authentication problems with service accounts
- Fixed Pub/Sub message processing
- Corrected Gmail API permission issues
- Fixed email processing filters

### 📚 Documentation Updates
- **README.md**: Complete rewrite with comprehensive documentation
- **CHANGELOG.md**: Added this changelog file
- **Code Comments**: Enhanced inline documentation
- **Setup Instructions**: Detailed deployment and configuration guides

### 🧪 Testing Improvements
- Multiple test scripts for different scenarios
- Debug utilities for troubleshooting
- Health check endpoints
- Comprehensive error logging

### 🔄 System Architecture Changes
- **Processing Flow**: 
  1. Gmail watch → Pub/Sub notification → Cloud Run processing
  2. Security validation → AI generation → Email reply → Label marking
- **Fallback Mechanism**: Graceful degradation when AI services are unavailable
- **Monitoring**: Enhanced logging and health checks

### ⚡ Performance Optimizations
- Streaming responses from GenAI SDK
- Optimized Pub/Sub message processing
- Reduced cold start times
- Efficient error handling

### 🔐 Security Hardening
- OAuth 2.0 with secure token storage
- Input validation and sanitization
- Rate limiting considerations
- Secure environment variable handling

---

## [1.0.0] - Initial Release

### Initial Features
- Basic Gmail API integration
- Simple auto-reply functionality
- Google Cloud Run deployment
- Basic Vertex AI integration

### Components
- `main.py` - Core Flask application
- `deploy.sh` - Deployment script
- `requirements.txt` - Dependencies
- Basic testing scripts

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
