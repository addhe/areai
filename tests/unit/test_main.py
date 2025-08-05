#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for main Cloud Function
"""

import base64
import json
import unittest
from unittest.mock import MagicMock, patch

from cloud_function.main import pubsub_trigger


class TestMainFunction(unittest.TestCase):
    """Test cases for main Cloud Function."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_data = {
            "historyId": "12345",
            "emailAddress": "user@example.com"
        }
        self.encoded_event = base64.b64encode(json.dumps(self.event_data).encode()).decode()
        self.context = MagicMock()
        self.email_content = {
            "subject": "Test Subject",
            "body": "This is a test email.",
            "from": "client@example.com",
            "message_id": "msg123"
        }
        self.customer_info = {
            "name": "John Doe",
            "status": "active",
            "customer_id": "CUS123456",
            "account_type": "premium"
        }
        self.ai_reply = "This is an AI-generated reply."

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.main.generate_ai_reply")
    @patch("cloud_function.main.send_reply")
    def test_pubsub_trigger_success(
        self, mock_send_reply, mock_generate_ai_reply, mock_initialize_vertex_ai,
        mock_verify_customer, mock_get_email_content, mock_initialize_gmail_service,
        mock_get_secret
    ):
        """Test successful execution of pubsub_trigger."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        mock_get_email_content.return_value = self.email_content
        mock_verify_customer.return_value = self.customer_info
        mock_generate_ai_reply.return_value = self.ai_reply
        mock_send_reply.return_value = True
        
        # Execute
        pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_get_secret.assert_called_once()
        mock_initialize_gmail_service.assert_called_once_with("test-secret")
        mock_get_email_content.assert_called_once_with(mock_gmail_service, "12345")
        mock_verify_customer.assert_called_once_with("client@example.com")
        mock_initialize_vertex_ai.assert_called_once()
        mock_generate_ai_reply.assert_called_once_with(
            "client@example.com", "Test Subject", "This is a test email.",
            "formal", self.customer_info
        )
        mock_send_reply.assert_called_once_with(
            mock_gmail_service, "client@example.com", "Test Subject", self.ai_reply
        )

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    def test_pubsub_trigger_no_email_content(
        self, mock_get_email_content, mock_initialize_gmail_service, mock_get_secret
    ):
        """Test pubsub_trigger with no email content."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        mock_get_email_content.return_value = None
        
        # Execute
        pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_get_secret.assert_called_once()
        mock_initialize_gmail_service.assert_called_once_with("test-secret")
        mock_get_email_content.assert_called_once_with(mock_gmail_service, "12345")

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.main.generate_ai_reply")
    @patch("cloud_function.main.send_reply")
    def test_pubsub_trigger_no_customer_info(
        self, mock_send_reply, mock_generate_ai_reply, mock_initialize_vertex_ai,
        mock_verify_customer, mock_get_email_content, mock_initialize_gmail_service,
        mock_get_secret
    ):
        """Test pubsub_trigger with no customer info."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        mock_get_email_content.return_value = self.email_content
        mock_verify_customer.return_value = None
        mock_generate_ai_reply.return_value = self.ai_reply
        mock_send_reply.return_value = True
        
        # Execute
        pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_verify_customer.assert_called_once_with("client@example.com")
        mock_generate_ai_reply.assert_called_once_with(
            "client@example.com", "Test Subject", "This is a test email.",
            "formal", None
        )
        mock_send_reply.assert_called_once_with(
            mock_gmail_service, "client@example.com", "Test Subject", self.ai_reply
        )

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.main.generate_ai_reply")
    @patch("cloud_function.main.send_reply")
    def test_pubsub_trigger_send_reply_failure(
        self, mock_send_reply, mock_generate_ai_reply, mock_initialize_vertex_ai,
        mock_verify_customer, mock_get_email_content, mock_initialize_gmail_service,
        mock_get_secret
    ):
        """Test pubsub_trigger with send reply failure."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        mock_get_email_content.return_value = self.email_content
        mock_verify_customer.return_value = self.customer_info
        mock_generate_ai_reply.return_value = self.ai_reply
        mock_send_reply.return_value = False
        
        # Execute
        pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_send_reply.assert_called_once_with(
            mock_gmail_service, "client@example.com", "Test Subject", self.ai_reply
        )

    @patch("cloud_function.main.get_secret")
    def test_pubsub_trigger_invalid_event(self, mock_get_secret):
        """Test pubsub_trigger with invalid event data."""
        # Setup
        invalid_event = {"data": base64.b64encode(b"invalid json").decode()}
        
        # Execute
        pubsub_trigger(invalid_event, self.context)
        
        # Verify
        mock_get_secret.assert_not_called()

    @patch("cloud_function.main.get_secret")
    def test_pubsub_trigger_missing_history_id(self, mock_get_secret):
        """Test pubsub_trigger with missing history ID."""
        # Setup
        invalid_data = {
            "emailAddress": "user@example.com"
            # Missing historyId
        }
        encoded_event = base64.b64encode(json.dumps(invalid_data).encode()).decode()
        
        # Execute
        pubsub_trigger({"data": encoded_event}, self.context)
        
        # Verify
        mock_get_secret.assert_not_called()


if __name__ == "__main__":
    unittest.main()
