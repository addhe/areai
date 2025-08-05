#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Customer API utility functions for Auto Reply Email system
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
API_ENDPOINT = os.environ.get("CUSTOMER_API_ENDPOINT", "https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah")
API_KEY = os.environ.get("CUSTOMER_API_KEY", "b7f2e1c4-9a3d-4e8b-8c2a-7d5e6f1a2b3c")
MAX_RETRIES = 3
RETRY_DELAY = 2


def verify_customer(email: str) -> Optional[Dict[str, Any]]:
    """Verify customer by email address.
    
    Args:
        email (str): Customer email address
        
    Returns:
        Optional[Dict[str, Any]]: Customer information if found, None otherwise
        
    Raises:
        ValueError: If API endpoint is not configured
        RuntimeError: If API request fails after retries
    """
    if not API_ENDPOINT:
        logger.error("Nasabah API endpoint not configured")
        raise ValueError("Nasabah API endpoint not configured")
    
    if not API_KEY:
        logger.error("Nasabah API key not configured")
        raise ValueError("Nasabah API key not configured")
    
    # Extract email address from "Name <email>" format if needed
    clean_email = email
    if "<" in email and ">" in email:
        clean_email = email.split("<")[1].split(">")[0]
    
    # Prepare request
    url = f"{API_ENDPOINT}?email={clean_email}"
    headers = {
        "Accept": "application/json",
        "x-api-key": API_KEY
    }
    
    # Make request with retries
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                nasabah = data["data"][0]
                logger.info(f"Nasabah verified: {clean_email}")
                
                # Convert to standard format for compatibility
                customer_data = {
                    "name": nasabah.get("nama"),
                    "status": nasabah.get("status"),
                    "customer_id": str(nasabah.get("id")),
                    "account_type": "premium" if nasabah.get("saldo", 0) >= 10000000 else "standard",
                    "saldo": nasabah.get("saldo", 0)
                }
                return customer_data
            else:
                logger.info(f"Nasabah not found: {clean_email}")
                return None
                
        except RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to verify nasabah after {MAX_RETRIES} attempts: {str(e)}")
                raise RuntimeError(f"Nasabah API request failed: {str(e)}")
            
            delay = RETRY_DELAY * (2 ** attempt)
            logger.info(f"API request failed, retrying in {delay} seconds")
            time.sleep(delay)
    
    return None


def get_mock_customer_data(email: str) -> Optional[Dict[str, Any]]:
    """Get mock customer data for testing.
    
    Args:
        email (str): Customer email address
        
    Returns:
        Optional[Dict[str, Any]]: Mock customer data
    """
    # Mock customer database
    mock_customers = {
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
    
    # Extract email address from "Name <email>" format if needed
    clean_email = email
    if "<" in email and ">" in email:
        clean_email = email.split("<")[1].split(">")[0]
    
    return mock_customers.get(clean_email)
