#!/usr/bin/env python3
"""
List Claude Models

This script lists the available Claude models.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_claude_models():
    """List the available Claude models."""
    try:
        from anthropic import Anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            return
            
        logger.info(f"API key found: {api_key[:5]}...")
        
        logger.info("Initializing Anthropic client...")
        client = Anthropic(api_key=api_key)
        
        # List of known Claude models to try
        known_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "claude-3",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
            "claude-instant-1.1",
            "claude-instant-1.0",
            "claude-3.5-sonnet",
            "claude-3.5-sonnet-20240620",
            "claude-3.5-sonnet-20240307",
            "claude-3.0-sonnet",
            "claude-3.0-sonnet-20240229",
            "claude-2",
            "claude-2.0",
            "claude-2.1",
            "claude-instant",
            "claude-instant-1",
            "claude-instant-1.0",
            "claude-instant-1.1",
            "claude-instant-1.2",
            "claude-3.7-sonnet",
            "claude-3.7-haiku",
            "claude-3.7-opus",
        ]
        
        logger.info("Testing known Claude models...")
        
        for model in known_models:
            try:
                logger.info(f"Testing model: {model}")
                # Try to create a simple message with the model
                message = client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[
                        {"role": "user", "content": "Hello"}
                    ]
                )
                logger.info(f"✅ Model {model} is available")
            except Exception as e:
                logger.error(f"❌ Model {model} is not available: {e}")
        
        logger.info("Finished testing Claude models")
        
    except Exception as e:
        logger.error(f"Error listing Claude models: {e}")

if __name__ == "__main__":
    list_claude_models() 