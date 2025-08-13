#!/usr/bin/env python3
"""
Debug script to test customer service module functionality
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_import():
    """Test config.py import"""
    try:
        import config
        logger.info("✅ Config import successful")
        logger.info(f"Config attributes: {dir(config)}")
        
        # Check if required attributes exist
        if hasattr(config, 'NASABAH_API_URL'):
            logger.info(f"✅ NASABAH_API_URL found: {config.NASABAH_API_URL}")
        else:
            logger.error("❌ NASABAH_API_URL not found in config")
            
        if hasattr(config, 'NASABAH_API_KEY'):
            logger.info("✅ NASABAH_API_KEY found (not showing value for security)")
        else:
            logger.error("❌ NASABAH_API_KEY not found in config")
            
        return True, config
    except ImportError as e:
        logger.error(f"❌ Config import failed: {e}")
        return False, None

def test_customer_service_import():
    """Test customer service module import"""
    try:
        from customer_service import get_customer_context
        logger.info("✅ Customer service import successful")
        return True, get_customer_context
    except ImportError as e:
        logger.error(f"❌ Customer service import failed: {e}")
        return False, None

def test_customer_api_call(get_customer_context_func):
    """Test actual API call to customer service"""
    test_email = "dyrrotheudora@gmail.com"
    logger.info(f"Testing customer API call for: {test_email}")
    
    try:
        is_nasabah, customer_info = get_customer_context_func(test_email)
        logger.info(f"✅ API call successful")
        logger.info(f"Is Nasabah: {is_nasabah}")
        logger.info(f"Customer Info: {customer_info}")
        return is_nasabah, customer_info
    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
        return False, {}

def main():
    logger.info("=== Customer Service Debug Test ===")
    
    # Test 1: Config import
    logger.info("\n1. Testing config import...")
    config_success, config_obj = test_config_import()
    
    # Test 2: Customer service import
    logger.info("\n2. Testing customer service import...")
    cs_success, get_customer_context_func = test_customer_service_import()
    
    # Test 3: API call (only if both imports successful)
    if config_success and cs_success:
        logger.info("\n3. Testing customer API call...")
        is_nasabah, customer_info = test_customer_api_call(get_customer_context_func)
        
        if is_nasabah:
            logger.info("🎉 SUCCESS: Customer found and verified!")
        else:
            logger.warning("⚠️  Customer not found or not verified")
    else:
        logger.error("❌ Skipping API test due to import failures")
    
    logger.info("\n=== Debug Test Complete ===")

if __name__ == "__main__":
    main()
