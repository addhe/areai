#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for Customer API utility functions
"""

import unittest
from unittest.mock import MagicMock, patch

import requests
from requests.exceptions import RequestException

from cloud_function.utils.customer_api import (
    verify_customer,
    get_mock_customer_data
)


class TestCustomerAPIUtils(unittest.TestCase):
    """Test cases for Customer API utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.email = "client@example.com"
        self.formatted_email = "John Doe <client@example.com>"
        self.customer_data = {
            "name": "John Doe",
            "status": "active",
            "customer_id": "CUS123456",
            "account_type": "premium"
        }

    @patch("cloud_function.utils.customer_api.requests.post")
    @patch("cloud_function.utils.customer_api.API_ENDPOINT", "https://api.example.com")
    def test_verify_customer_success(self, mock_post):
        """Test verifying customer successfully."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "customer": self.customer_data
        }
        mock_post.return_value = mock_response
        
        # Execute
        result = verify_customer(self.email)
        
        # Verify
        mock_post.assert_called_once_with(
            "https://api.example.com/verify",
            json={"email": self.email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        self.assertEqual(result, self.customer_data)

    @patch("cloud_function.utils.customer_api.requests.post")
    @patch("cloud_function.utils.customer_api.API_ENDPOINT", "https://api.example.com")
    def test_verify_customer_formatted_email(self, mock_post):
        """Test verifying customer with formatted email."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "customer": self.customer_data
        }
        mock_post.return_value = mock_response
        
        # Execute
        result = verify_customer(self.formatted_email)
        
        # Verify
        mock_post.assert_called_once_with(
            "https://api.example.com/verify",
            json={"email": "client@example.com"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        self.assertEqual(result, self.customer_data)

    @patch("cloud_function.utils.customer_api.requests.post")
    @patch("cloud_function.utils.customer_api.API_ENDPOINT", "https://api.example.com")
    def test_verify_customer_not_found(self, mock_post):
        """Test verifying customer not found."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "message": "Customer not found"
        }
        mock_post.return_value = mock_response
        
        # Execute
        result = verify_customer(self.email)
        
        # Verify
        mock_post.assert_called_once()
        self.assertIsNone(result)

    @patch("cloud_function.utils.customer_api.requests.post")
    @patch("cloud_function.utils.customer_api.API_ENDPOINT", "https://api.example.com")
    @patch("cloud_function.utils.customer_api.time.sleep")
    def test_verify_customer_retry(self, mock_sleep, mock_post):
        """Test verifying customer with retry."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "customer": self.customer_data
        }
        mock_post.side_effect = [
            RequestException("Connection error"),
            mock_response
        ]
        
        # Execute
        result = verify_customer(self.email)
        
        # Verify
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once()
        self.assertEqual(result, self.customer_data)

    @patch("cloud_function.utils.customer_api.requests.post")
    @patch("cloud_function.utils.customer_api.API_ENDPOINT", "https://api.example.com")
    def test_verify_customer_max_retries(self, mock_post):
        """Test verifying customer with max retries."""
        # Setup
        mock_post.side_effect = RequestException("Connection error")
        
        # Execute and Verify
        with self.assertRaises(RuntimeError):
            verify_customer(self.email)

    @patch("cloud_function.utils.customer_api.API_ENDPOINT", None)
    def test_verify_customer_no_endpoint(self):
        """Test verifying customer with no endpoint."""
        # Execute and Verify
        with self.assertRaises(ValueError):
            verify_customer(self.email)

    def test_get_mock_customer_data_found(self):
        """Test getting mock customer data found."""
        # Execute
        result = get_mock_customer_data("client@example.com")
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["status"], "active")

    def test_get_mock_customer_data_formatted_email(self):
        """Test getting mock customer data with formatted email."""
        # Execute
        result = get_mock_customer_data("John Doe <client@example.com>")
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "John Doe")

    def test_get_mock_customer_data_not_found(self):
        """Test getting mock customer data not found."""
        # Execute
        result = get_mock_customer_data("unknown@example.com")
        
        # Verify
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
