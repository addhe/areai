#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for Auto Reply Email system
"""

import base64
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from cloud_function.main import pubsub_trigger
from cloud_function.utils.customer_api import get_mock_customer_data
from cloud_function.utils.gmail import get_email_content, send_reply
from cloud_function.utils.vertex_ai import generate_ai_reply


class TestEmailFlow(unittest.TestCase):
    """Integration test for email processing flow."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        os.environ["GCP_PROJECT_ID"] = "test-project"
        os.environ["GCP_REGION"] = "us-central1"
        os.environ["CUSTOMER_API_ENDPOINT"] = "https://api.example.com"
        os.environ["USE_MOCK_CUSTOMER_DATA"] = "true"
        
        # Test data
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

    def tearDown(self):
        """Clean up after tests."""
        # Remove environment variables
        for env_var in ["GCP_PROJECT_ID", "GCP_REGION", "CUSTOMER_API_ENDPOINT", "USE_MOCK_CUSTOMER_DATA"]:
            if env_var in os.environ:
                del os.environ[env_var]

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.main.generate_ai_reply")
    @patch("cloud_function.main.send_reply")
    def test_end_to_end_flow(
        self, mock_send_reply, mock_generate_ai_reply, mock_initialize_vertex_ai,
        mock_verify_customer, mock_get_email_content, mock_initialize_gmail_service,
        mock_get_secret
    ):
        """Test end-to-end email processing flow."""
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
        
        # Verify full flow
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
    @patch("cloud_function.utils.gmail.get_history")
    @patch("cloud_function.utils.gmail.get_message")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.main.generate_ai_reply")
    @patch("cloud_function.main.send_reply")
    def test_integration_with_real_functions(
        self, mock_send_reply, mock_generate_ai_reply, mock_initialize_vertex_ai,
        mock_verify_customer, mock_get_message, mock_get_history, 
        mock_initialize_gmail_service, mock_get_secret
    ):
        """Test integration with real utility functions."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        
        # Mock Gmail API responses
        mock_history = {
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
        mock_get_history.return_value = mock_history
        
        mock_message = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "client@example.com"}
                ],
                "body": {
                    "data": base64.b64encode(b"This is a test email.").decode()
                }
            }
        }
        mock_get_message.return_value = mock_message
        
        # Use real customer API function with mock data
        mock_verify_customer.side_effect = get_mock_customer_data
        
        mock_initialize_vertex_ai.return_value = None
        mock_generate_ai_reply.return_value = self.ai_reply
        mock_send_reply.return_value = True
        
        # Execute - use real get_email_content function
        with patch("cloud_function.main.get_email_content", wraps=get_email_content):
            pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_get_history.assert_called_once()
        mock_get_message.assert_called_once()
        mock_verify_customer.assert_called_once()
        mock_initialize_vertex_ai.assert_called_once()
        mock_generate_ai_reply.assert_called_once()
        mock_send_reply.assert_called_once()

    @patch("cloud_function.main.get_secret")
    @patch("cloud_function.main.initialize_gmail_service")
    @patch("cloud_function.main.get_email_content")
    @patch("cloud_function.main.verify_customer")
    @patch("cloud_function.main.initialize_vertex_ai")
    @patch("cloud_function.utils.vertex_ai.create_prompt")
    @patch("cloud_function.utils.vertex_ai.aiplatform.GenerativeModel")
    @patch("cloud_function.main.send_reply")
    def test_integration_with_real_ai_prompt(
        self, mock_send_reply, mock_generative_model, mock_create_prompt,
        mock_initialize_vertex_ai, mock_verify_customer, mock_get_email_content,
        mock_initialize_gmail_service, mock_get_secret
    ):
        """Test integration with real AI prompt generation."""
        # Setup
        mock_get_secret.return_value = "test-secret"
        mock_gmail_service = MagicMock()
        mock_initialize_gmail_service.return_value = mock_gmail_service
        mock_get_email_content.return_value = self.email_content
        mock_verify_customer.return_value = self.customer_info
        
        # Use real prompt creation
        from cloud_function.utils.vertex_ai import create_prompt
        mock_create_prompt.side_effect = create_prompt
        
        # Mock Vertex AI response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = self.ai_reply
        mock_model.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model
        
        mock_send_reply.return_value = True
        
        # Execute - use real generate_ai_reply function
        with patch("cloud_function.main.generate_ai_reply", wraps=generate_ai_reply):
            pubsub_trigger({"data": self.encoded_event}, self.context)
        
        # Verify
        mock_create_prompt.assert_called_once()
        mock_model.generate_content.assert_called_once()
        self.assertIn("Pengirim", mock_create_prompt.call_args[0][2])  # Check prompt contains sender
        mock_send_reply.assert_called_once()


if __name__ == "__main__":
    unittest.main()
