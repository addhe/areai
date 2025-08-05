#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for Vertex AI utility functions
"""

import unittest
from unittest.mock import MagicMock, patch

from google.api_core import exceptions as gcp_exceptions

from cloud_function.utils.vertex_ai import (
    initialize_vertex_ai,
    create_prompt,
    generate_ai_reply,
    get_fallback_reply
)


class TestVertexAIUtils(unittest.TestCase):
    """Test cases for Vertex AI utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.sender = "sender@example.com"
        self.subject = "Test Subject"
        self.body = "This is a test email body."
        self.tone = "formal"
        self.customer_info = {
            "name": "John Doe",
            "status": "active",
            "customer_id": "CUS123456",
            "account_type": "premium"
        }

    @patch("cloud_function.utils.vertex_ai.aiplatform")
    def test_initialize_vertex_ai(self, mock_aiplatform):
        """Test initializing Vertex AI."""
        # Execute
        initialize_vertex_ai("test-project", "us-central1")
        
        # Verify
        mock_aiplatform.init.assert_called_once_with(
            project="test-project", location="us-central1"
        )

    def test_create_prompt_without_customer_info(self):
        """Test creating a prompt without customer info."""
        # Execute
        result = create_prompt(
            self.sender, self.subject, self.body, self.tone
        )
        
        # Verify
        self.assertIn(self.sender, result)
        self.assertIn(self.subject, result)
        self.assertIn(self.body, result)
        self.assertIn(self.tone, result)
        self.assertNotIn("Nama pelanggan", result)

    def test_create_prompt_with_customer_info(self):
        """Test creating a prompt with customer info."""
        # Execute
        result = create_prompt(
            self.sender, self.subject, self.body, self.tone, self.customer_info
        )
        
        # Verify
        self.assertIn(self.sender, result)
        self.assertIn(self.subject, result)
        self.assertIn(self.body, result)
        self.assertIn(self.tone, result)
        self.assertIn("John Doe", result)
        self.assertIn("active", result)

    @patch("cloud_function.utils.vertex_ai.aiplatform.GenerativeModel")
    def test_generate_ai_reply_success(self, mock_generative_model):
        """Test generating AI reply successfully."""
        # Setup
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is an AI generated reply."
        mock_model.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model
        
        # Execute
        result = generate_ai_reply(
            self.sender, self.subject, self.body, self.tone, self.customer_info
        )
        
        # Verify
        self.assertEqual(result, "This is an AI generated reply.")
        mock_model.generate_content.assert_called_once()

    @patch("cloud_function.utils.vertex_ai.aiplatform.GenerativeModel")
    @patch("cloud_function.utils.vertex_ai.time.sleep")
    def test_generate_ai_reply_retry(self, mock_sleep, mock_generative_model):
        """Test generating AI reply with retry."""
        # Setup
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is an AI generated reply."
        mock_model.generate_content.side_effect = [
            gcp_exceptions.ResourceExhausted("Rate limit"),
            mock_response
        ]
        mock_generative_model.return_value = mock_model
        
        # Execute
        result = generate_ai_reply(
            self.sender, self.subject, self.body, self.tone, self.customer_info
        )
        
        # Verify
        self.assertEqual(result, "This is an AI generated reply.")
        self.assertEqual(mock_model.generate_content.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("cloud_function.utils.vertex_ai.aiplatform.GenerativeModel")
    def test_generate_ai_reply_fallback(self, mock_generative_model):
        """Test generating AI reply with fallback."""
        # Setup
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_generative_model.return_value = mock_model
        
        # Execute
        result = generate_ai_reply(
            self.sender, self.subject, self.body, self.tone, self.customer_info
        )
        
        # Verify
        self.assertEqual(result, get_fallback_reply())
        mock_model.generate_content.assert_called_once()

    def test_get_fallback_reply(self):
        """Test getting fallback reply."""
        # Execute
        result = get_fallback_reply()
        
        # Verify
        self.assertIn("Terima kasih", result)
        self.assertIn("mohon maaf", result.lower())


if __name__ == "__main__":
    unittest.main()
