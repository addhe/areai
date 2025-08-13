"""
Customer Service Module
Handles customer verification and data retrieval from Nasabah API
"""

import logging
import requests
import re

# Configure logging
logger = logging.getLogger(__name__)

# Import config with environment variable fallback
import os

config = None
try:
    from functions.auto_reply import config
    logger.info("Successfully imported config.py in customer_service module (absolute import)")
except ImportError:
    try:
        import config
        logger.info("Successfully imported config.py in customer_service module (relative import)")
    except ImportError:
        logger.info("Config.py not available, using environment variables")
        # Create a simple config object from environment variables
        class Config:
            NASABAH_API_URL = os.getenv('NASABAH_API_URL', 'https://nasabah-api-361046956504.asia-southeast2.run.app/nasabah')
            NASABAH_API_KEY = os.getenv('NASABAH_API_KEY', '')
        
        config = Config()
        logger.info(f"Using environment config - API URL: {config.NASABAH_API_URL}")
        if config.NASABAH_API_KEY:
            logger.info("API key found in environment variables")
        else:
            logger.warning("No API key found in environment variables")


def normalize_email(email):
    """Normalize email address for consistent comparison."""
    if not email:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = email.lower().strip()
    
    # Remove any angle brackets or display names
    # Extract email from formats like "Name <email@domain.com>"
    email_match = re.search(r'<([^>]+)>', normalized)
    if email_match:
        normalized = email_match.group(1)
    
    # Additional cleanup
    normalized = normalized.strip('<>')
    
    return normalized


def check_customer_status(sender_email):
    """
    Check if sender is a verified customer and get their data.
    
    Args:
        sender_email (str): Email address of the sender
        
    Returns:
        tuple: (is_customer, customer_data)
            - is_customer (bool): True if verified customer
            - customer_data (dict): Customer data from API or None
    """
    logger.info(f"Starting customer status check for: {sender_email}")
    
    # Normalize email for consistent comparison
    normalized_email = normalize_email(sender_email)
    logger.info(f"Normalized email: {normalized_email}")
    
    # Return early if email is empty after normalization
    if not normalized_email:
        logger.warning("Empty email after normalization, cannot check customer status")
        return False, None
        
    try:
        # Check if config is available
        if not config:
            logger.error("Config not available, skipping customer API check")
            return False, None
        
        logger.info(f"Config available - Using API URL: {config.NASABAH_API_URL}")
        logger.info(f"Checking customer status for email: {normalized_email}")
        
        # Prepare API request
        headers = {
            'x-api-key': config.NASABAH_API_KEY,
            'Accept': 'application/json'
        }
        params = {'email': normalized_email}
        
        logger.info(f"Making API request to: {config.NASABAH_API_URL}")
        logger.info(f"Request params: {params}")
        
        # Make API request
        response = requests.get(config.NASABAH_API_URL, headers=headers, params=params, timeout=5)
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Headers: {dict(response.headers)}")
        logger.info(f"API Response Text: {response.text}")

        # Try to parse JSON response
        response_data = None
        try:
            if response.text and response.text.strip():
                response_data = response.json()
                logger.info(f"Parsed JSON response: {response_data}")
        except ValueError as e:
            logger.error(f"Error parsing JSON response: {e} - Raw response: {response.text}")

        # Status 200 with valid data
        if response.status_code == 200 and response_data:
            if 'data' in response_data and isinstance(response_data['data'], list):
                if len(response_data['data']) > 0:
                    customer_data = response_data['data'][0]
                    logger.info(f"Customer found: {customer_data.get('nama', 'Unknown')} - Status: {customer_data.get('status', 'Unknown')}")
                    return True, response_data
                else:
                    logger.info(f"No customer data found for email: {normalized_email}")
                    return False, None
            else:
                logger.warning(f"Unexpected response format: {response_data}")
                return False, None
        
        # Status 404 or other error codes
        elif response.status_code == 404:
            logger.info(f"Customer not found (404) for email: {normalized_email}")
            return False, None
        else:
            logger.warning(f"API returned status {response.status_code}: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        logger.error("Timeout calling customer API")
        return False, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling customer API: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error in customer status check: {e}", exc_info=True)
        return False, None


def extract_customer_info(customer_data):
    """
    Extract and format customer information for AI prompt.
    
    Args:
        customer_data (dict): Raw customer data from API
        
    Returns:
        dict: Formatted customer information
    """
    if not customer_data or not isinstance(customer_data, dict):
        return {
            'name': 'Nasabah',
            'status': 'unknown',
            'saldo_info': ''
        }
    
    try:
        # Handle nested data structure
        if 'data' in customer_data and isinstance(customer_data['data'], list) and len(customer_data['data']) > 0:
            customer_data = customer_data['data'][0]
        
        # Extract basic info
        name = customer_data.get('nama', 'Nasabah')
        status = customer_data.get('status', 'unknown')
        
        # Extract and format saldo
        saldo_info = ""
        if 'saldo' in customer_data:
            saldo_value = customer_data['saldo']
            try:
                # Format saldo with thousand separators
                formatted_saldo = "{:,}".format(int(saldo_value)).replace(',', '.')
                saldo_info = f"\n- Saldo Anda: Rp {formatted_saldo}"
                logger.info(f"Extracted saldo: {saldo_value}, formatted as: {formatted_saldo}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error formatting saldo: {e}")
        elif 'balance' in customer_data:
            saldo_value = customer_data['balance']
            try:
                # Format saldo with thousand separators
                formatted_saldo = "{:,}".format(int(saldo_value)).replace(',', '.')
                saldo_info = f"\n- Saldo Anda: Rp {formatted_saldo}"
                logger.info(f"Extracted balance: {saldo_value}, formatted as: {formatted_saldo}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error formatting balance: {e}")
        
        return {
            'name': name,
            'status': status,
            'saldo_info': saldo_info
        }
        
    except Exception as e:
        logger.error(f"Error extracting customer info: {e}", exc_info=True)
        return {
            'name': 'Nasabah',
            'status': 'unknown',
            'saldo_info': ''
        }


def get_customer_context(sender_email):
    """
    Get complete customer context for AI prompt generation.
    
    Args:
        sender_email (str): Email address of the sender
        
    Returns:
        tuple: (is_customer, customer_info_dict)
    """
    logger.info(f"Getting customer context for: {sender_email}")
    
    # Check customer status
    is_customer, customer_data = check_customer_status(sender_email)
    
    # Extract customer information
    customer_info = extract_customer_info(customer_data)
    
    logger.info(f"Customer context result - Is Customer: {is_customer}, Info: {customer_info}")
    
    return is_customer, customer_info
