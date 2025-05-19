"""
Test script for ZentraChatbot fallback model functionality.
This script tests the fallback mode to ensure it works correctly
when deployed to Heroku without API keys.
"""

import os
import sys
import unittest
from unittest import mock
import logging
from app.fallback_model import FallbackModel, get_fallback_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFallbackModel(unittest.TestCase):
    """Test cases for the fallback model functionality."""

    def setUp(self):
        """Set up test environment with mocked environment variables."""
        # Mock Heroku environment
        self.env_patcher = mock.patch.dict(os.environ, {
            "HEROKU_APP_NAME": "zentrachatbot-test"
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    def test_fallback_model_initialization(self):
        """Test that the fallback model initializes correctly."""
        model = FallbackModel(model_name="distilgpt2")  # Use smaller model for faster testing

        # Mock the actual model loading to avoid downloading during tests
        with mock.patch('transformers.pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock.MagicMock()
            success = model.initialize()

            self.assertTrue(success)
            mock_pipeline.assert_called_once()

    def test_minimal_resources_mode(self):
        """Test that minimal resources mode selects the correct model."""
        # Set minimal resources flag
        with mock.patch.dict(os.environ, {"MINIMAL_RESOURCES": "true"}):
            model = get_fallback_model()
            self.assertEqual(model.model_name, "distilgpt2")
            self.assertEqual(model.max_length, 512)

    def test_default_model_selection(self):
        """Test that the default model is selected correctly."""
        model = get_fallback_model()
        self.assertEqual(model.model_name, "EleutherAI/gpt-neo-1.3B")
        self.assertEqual(model.max_length, 1024)

    def test_custom_model_selection(self):
        """Test that a custom model can be specified."""
        with mock.patch.dict(os.environ, {"FALLBACK_MODEL_NAME": "EleutherAI/gpt-neo-125M"}):
            model = get_fallback_model()
            self.assertEqual(model.model_name, "EleutherAI/gpt-neo-125M")

    @mock.patch('app.fallback_model.FallbackModel.generate')
    def test_model_generate_called(self, mock_generate):
        """Test that the generate method is called correctly."""
        mock_generate.return_value = "Test response"

        model = FallbackModel()
        result = model("Test prompt")

        mock_generate.assert_called_once_with("Test prompt")
        self.assertEqual(result, "Test response")

    @mock.patch('app.fallback_model.FallbackModel.initialize')
    def test_initialization_failure(self, mock_initialize):
        """Test behavior when initialization fails."""
        mock_initialize.return_value = False

        model = FallbackModel()
        result = model.generate("Test prompt")

        self.assertIn("unable to process", result)

if __name__ == "__main__":
    unittest.main()
