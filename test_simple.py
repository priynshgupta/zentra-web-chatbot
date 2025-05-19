"""
Simple test script to verify the fallback model can be initialized.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the fallback model
try:
    from app.fallback_model import get_fallback_model

    # Test initialization with minimal model for faster testing
    logger.info("Testing fallback model initialization with distilgpt2...")
    model = get_fallback_model(model_name="distilgpt2")

    # Test generation with a simple prompt
    logger.info("Testing generation with a simple prompt...")
    response = model("Hello, my name is Alice. What's your name?")

    logger.info(f"Response received (length: {len(response)})")
    logger.info(f"Sample output: {response[:100]}...")

    logger.info("Test completed successfully!")
except Exception as e:
    logger.error(f"Error testing fallback model: {e}")
    sys.exit(1)
