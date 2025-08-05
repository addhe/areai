#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vertex AI utility functions for Auto Reply Email system
"""

import logging
import time
from typing import Dict, Any, Optional

from google.cloud import aiplatform
from google.api_core import exceptions as gcp_exceptions

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
MODEL_NAME = "gemini-1.5-pro"
MAX_RETRIES = 3
RETRY_DELAY = 2


def initialize_vertex_ai(project_id: str, location: str = "us-central1") -> None:
    """Initialize Vertex AI client.
    
    Args:
        project_id (str): GCP project ID
        location (str): GCP region
    """
    try:
        aiplatform.init(project=project_id, location=location)
        logger.info("Vertex AI initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI: {str(e)}")
        raise


def create_prompt(sender: str, subject: str, body: str, tone: str, 
                  customer_info: Optional[Dict[str, Any]] = None) -> str:
    """Create prompt for Vertex AI Gemini.
    
    Args:
        sender (str): Email sender
        subject (str): Email subject
        body (str): Email body
        tone (str): Reply tone (formal/casual)
        customer_info (Optional[Dict[str, Any]]): Customer information if available
        
    Returns:
        str: Formatted prompt
    """
    # Base prompt template
    prompt = f"""
    Anda adalah asisten email profesional. 
    Tugas Anda adalah membalas email masuk dengan jawaban yang sopan, singkat, dan jelas. 
    Gunakan gaya bahasa {tone}.
    
    Berikut detail email yang masuk:
    - Pengirim: {sender}
    - Subjek: {subject}
    - Isi email: 
    {body}
    """
    
    # Add customer information if available
    if customer_info:
        customer_name = customer_info.get("name", "")
        customer_status = customer_info.get("status", "")
        
        prompt += f"""
    Informasi tambahan:
    - Nama pelanggan: {customer_name}
    - Status pelanggan: {customer_status}
        """
        
        # Personalization instruction
        prompt += f"""
    Sertakan nama pelanggan ({customer_name}) di awal balasan untuk personalisasi.
        """
    
    # Final instructions
    prompt += f"""
    Balas email ini dengan nada {tone}. 
    Jangan sertakan tanda tangan pribadi.
    Balasan tidak boleh lebih dari 150 kata.
    Selalu ucapkan terima kasih di awal balasan.
    """
    
    return prompt


def generate_ai_reply(sender: str, subject: str, body: str, tone: str,
                     customer_info: Optional[Dict[str, Any]] = None) -> str:
    """Generate AI reply using Vertex AI Gemini.
    
    Args:
        sender (str): Email sender
        subject (str): Email subject
        body (str): Email body
        tone (str): Reply tone (formal/casual)
        customer_info (Optional[Dict[str, Any]]): Customer information if available
        
    Returns:
        str: Generated reply text
    """
    # Create prompt
    prompt = create_prompt(sender, subject, body, tone, customer_info)
    
    # Initialize Vertex AI model
    try:
        model = aiplatform.GenerativeModel(MODEL_NAME)
        
        # Generate content with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except gcp_exceptions.ResourceExhausted:
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries reached for AI generation")
                    return get_fallback_reply()
                delay = RETRY_DELAY * (2 ** attempt)
                logger.info(f"Rate limited, retrying in {delay} seconds")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Error generating AI reply: {str(e)}")
                return get_fallback_reply()
                
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI model: {str(e)}")
        return get_fallback_reply()


def get_fallback_reply() -> str:
    """Get fallback reply when AI generation fails.
    
    Returns:
        str: Fallback reply text
    """
    return """
    Terima kasih atas email Anda. Kami sudah menerimanya dan akan segera menindaklanjuti.
    
    Mohon maaf atas ketidaknyamanan ini. Tim kami akan menghubungi Anda dalam waktu 24 jam kerja.
    """
