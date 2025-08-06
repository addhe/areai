#!/usr/bin/env python3
"""
Test script untuk menguji berbagai skenario respons API Nasabah
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Import fungsi yang akan diuji
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import check_is_nasabah

class TestNasabahAPI(unittest.TestCase):
    """
    Test case untuk fungsi check_is_nasabah dengan berbagai skenario respons API
    """
    
    @patch('requests.get')
    def test_successful_response_with_explicit_status(self, mock_get):
        """Test ketika API mengembalikan status 200 dengan flag is_nasabah=True"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({'is_nasabah': True, 'customer_id': '12345', 'saldo': '15000000'})
        mock_response.json.return_value = {'is_nasabah': True, 'customer_id': '12345', 'saldo': '15000000'}
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertTrue(is_nasabah)
        self.assertIsNotNone(customer_data)
        self.assertEqual(customer_data['saldo'], '15000000')
    
    @patch('requests.get')
    def test_successful_response_without_explicit_status(self, mock_get):
        """Test ketika API mengembalikan status 200 tanpa flag is_nasabah"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({'customer_id': '12345', 'balance': '15000000'})
        mock_response.json.return_value = {'customer_id': '12345', 'balance': '15000000'}
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertTrue(is_nasabah)
        self.assertIsNotNone(customer_data)
        self.assertEqual(customer_data['balance'], '15000000')
    
    @patch('requests.get')
    def test_successful_response_with_explicit_non_customer(self, mock_get):
        """Test ketika API mengembalikan status 200 dengan flag is_nasabah=False"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({'is_nasabah': False})
        mock_response.json.return_value = {'is_nasabah': False}
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)
    
    @patch('requests.get')
    def test_not_found_response(self, mock_get):
        """Test ketika API mengembalikan status 404"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)
    
    @patch('requests.get')
    def test_error_response(self, mock_get):
        """Test ketika API mengembalikan status error"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)
    
    @patch('requests.get')
    def test_malformed_json_response(self, mock_get):
        """Test ketika API mengembalikan JSON yang tidak valid"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Not a valid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)
    
    @patch('requests.get')
    def test_empty_response(self, mock_get):
        """Test ketika API mengembalikan respons kosong"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)
    
    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test ketika terjadi error koneksi"""
        # Setup mock to raise an exception
        mock_get.side_effect = Exception("Connection error")
        
        # Call the function
        is_nasabah, customer_data = check_is_nasabah('test@example.com')
        
        # Assert
        self.assertFalse(is_nasabah)
        self.assertIsNone(customer_data)

if __name__ == "__main__":
    unittest.main()
