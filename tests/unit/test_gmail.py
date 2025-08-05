#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for Gmail utility functions
"""

import base64
import json
import unittest
from unittest.mock import MagicMock, patch

from google.api_core import exceptions as gcp_exceptions
from googleapiclient.errors import HttpError

from cloud_function.utils.gmail import (
    initialize_gmail_service,
    retry_with_backoff,
    get_message,
    get_email_content,
    create_message,
    send_reply
)


class TestGmailUtils(unittest.TestCase):
    """Test cases for Gmail utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_credentials = {
            "token": "test-token",
            "refresh_token": "test-refresh-token",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        self.mock_service = MagicMock()
        self.mock_message = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"}
                ],
                "body": {
                    "data": base64.urlsafe_b64encode(b"Test body").decode()
                }
            }
        }
        self.mock_history = {
            "history": [
                {
                    "messagesAdded": [
                        {
                            "message": {
                                "id": "msg123",
                                "internalDate": "1620000000000"
                            }
                        }
                    ]
                }
            ]
        }

    @patch("cloud_function.utils.gmail.Credentials")
    @patch("cloud_function.utils.gmail.build")
    def test_initialize_gmail_service(self, mock_build, mock_credentials):
        """Test initializing Gmail service."""
        # Setup
        mock_credentials.from_authorized_user_info.return_value = "test-creds"
        mock_build.return_value = "test-service"
        
        # Execute
        result = initialize_gmail_service(json.dumps(self.mock_credentials))
        
        # Verify
        mock_credentials.from_authorized_user_info.assert_called_once_with(self.mock_credentials)
        mock_build.assert_called_once_with("gmail", "v1", credentials="test-creds")
        self.assertEqual(result, "test-service")

    def test_retry_with_backoff_success(self):
        """Test retry with backoff succeeds on first try."""
        # Setup
        mock_func = MagicMock(return_value="success")
        
        # Execute
        result = retry_with_backoff(mock_func)
        
        # Verify
        mock_func.assert_called_once()
        self.assertEqual(result, "success")

    @patch("cloud_function.utils.gmail.time.sleep")
    def test_retry_with_backoff_resource_exhausted(self, mock_sleep):
        """Test retry with backoff handles ResourceExhausted."""
        # Setup
        mock_func = MagicMock()
        mock_func.side_effect = [
            gcp_exceptions.ResourceExhausted("Rate limit"),
            "success"
        ]
        
        # Execute
        result = retry_with_backoff(mock_func)
        
        # Verify
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once()
        self.assertEqual(result, "success")

    @patch("cloud_function.utils.gmail.retry_with_backoff")
    def test_get_message(self, mock_retry):
        """Test getting a message."""
        # Setup
        mock_service = MagicMock()
        mock_retry.return_value = self.mock_message
        
        # Execute
        result = get_message(mock_service, "msg123")
        
        # Verify
        self.assertEqual(result, self.mock_message)

    @patch("cloud_function.utils.gmail.get_history")
    @patch("cloud_function.utils.gmail.get_message")
    def test_get_email_content(self, mock_get_message, mock_get_history):
        """Test getting email content."""
        # Setup
        mock_service = MagicMock()
        mock_get_history.return_value = self.mock_history
        mock_get_message.return_value = self.mock_message
        
        # Execute
        result = get_email_content(mock_service, "hist123")
        
        # Verify
        self.assertEqual(result["subject"], "Test Subject")
        self.assertEqual(result["from"], "sender@example.com")
        self.assertEqual(result["message_id"], "msg123")
        self.assertTrue("body" in result)

    def test_create_message(self):
        """Test creating an email message."""
        # Execute
        result = create_message("recipient@example.com", "Test Subject", "Test body")
        
        # Verify
        self.assertTrue("raw" in result)
        
    @patch("cloud_function.utils.gmail.retry_with_backoff")
    def test_send_reply(self, mock_retry):
        """Test sending a reply."""
        # Setup
        mock_service = MagicMock()
        mock_retry.return_value = {"id": "msg456"}
        
        # Execute
        result = send_reply(mock_service, "recipient@example.com", "Test Subject", "Test reply")
        
        # Verify
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
