#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration settings for Auto Reply Email system
"""

import os
from typing import Dict, Any

# Project settings
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
REGION = os.environ.get("GCP_REGION", "us-central1")

# Gmail API settings
GMAIL_WATCH_TOPIC = f"projects/{PROJECT_ID}/topics/new-email"
GMAIL_OAUTH_SECRET = "gmail-oauth-token"

# Customer API settings
CUSTOMER_API_ENDPOINT = os.environ.get("CUSTOMER_API_ENDPOINT")
CUSTOMER_API_SECRET = "customer-api-key"

# Vertex AI settings
MODEL_NAME = "gemini-1.5-pro"
DEFAULT_TONE = "formal"

# Email settings
MAX_RETRY_COUNT = 3
REPLY_TIMEOUT_SECONDS = 15
DESTINATION_EMAIL = os.environ.get("DESTINATION_EMAIL", "addhe.warman+cs@gmail.com")

# Logging settings
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Feature flags
ENABLE_CUSTOMER_VERIFICATION = os.environ.get("ENABLE_CUSTOMER_VERIFICATION", "true").lower() == "true"
USE_MOCK_CUSTOMER_DATA = os.environ.get("USE_MOCK_CUSTOMER_DATA", "false").lower() == "true"

def get_config() -> Dict[str, Any]:
    """Get configuration settings.
    
    Returns:
        Dict[str, Any]: Configuration settings
    """
    return {
        "project": {
            "id": PROJECT_ID,
            "region": REGION
        },
        "gmail": {
            "watch_topic": GMAIL_WATCH_TOPIC,
            "oauth_secret": GMAIL_OAUTH_SECRET
        },
        "customer_api": {
            "endpoint": CUSTOMER_API_ENDPOINT,
            "secret": CUSTOMER_API_SECRET,
            "enabled": ENABLE_CUSTOMER_VERIFICATION,
            "use_mock": USE_MOCK_CUSTOMER_DATA
        },
        "vertex_ai": {
            "model": MODEL_NAME,
            "default_tone": DEFAULT_TONE
        },
        "email": {
            "max_retries": MAX_RETRY_COUNT,
            "timeout": REPLY_TIMEOUT_SECONDS,
            "destination": DESTINATION_EMAIL
        },
        "logging": {
            "level": LOG_LEVEL
        }
    }
