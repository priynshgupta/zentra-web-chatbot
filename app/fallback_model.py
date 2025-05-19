"""
Fallback model implementation for ZentraChatbot when deployed without API keys.
This module provides a simplified interaction with lightweight models
from the Hugging Face Transformers library.
"""

import os
import logging
from transformers import pipeline, set_seed
import torch

logger = logging.getLogger(__name__)

class FallbackModel:
    """
    A fallback LLM implementation using lightweight models
    from Hugging Face's Transformers library.
    """

    def __init__(self, model_name=None, max_length=1024, temperature=0.7):
        """Initialize the fallback model with configurable parameters."""
        self.model_name = model_name or os.environ.get("FALLBACK_MODEL_NAME", "EleutherAI/gpt-neo-1.3B")
        self.max_length = max_length
        self.temperature = temperature
        self.generator = None

        # Set seed for reproducibility
        set_seed(42)

    def initialize(self):
        """Lazy initialization of the model to save resources."""
        if self.generator is not None:
            return

        try:
            logger.info(f"Initializing fallback model: {self.model_name}")

            # Check for available hardware
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Using device: {'CUDA' if device == 0 else 'CPU'}")

            # Initialize with memory optimization settings
            self.generator = pipeline(
                'text-generation',
                model=self.model_name,
                device=device,
                model_kwargs={
                    "low_cpu_mem_usage": True,
                    "torch_dtype": torch.float16 if torch.cuda.is_available() else None
                }
            )
            logger.info("Fallback model initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing fallback model: {e}")
            return False

    def generate(self, prompt, **kwargs):
        """Generate text completion for the given prompt."""
        if not self.initialize():
            return "I apologize, but I'm unable to process your request due to technical limitations."

        try:
            # Merge default parameters with any provided kwargs
            params = {
                "max_length": self.max_length + len(prompt) // 4,  # Adjust based on prompt length
                "do_sample": True,
                "temperature": self.temperature,
                "top_k": 50,
                "top_p": 0.95,
                "repetition_penalty": 1.1,
                "num_return_sequences": 1,
                "pad_token_id": 50256  # Ensure proper padding
            }
            params.update(kwargs)

            # Generate text
            result = self.generator(prompt, **params)

            # Extract only the newly generated text, removing the original prompt
            generated_text = result[0]['generated_text'][len(prompt):]
            return generated_text
        except Exception as e:
            logger.error(f"Error generating text with fallback model: {e}")
            return "I apologize, but I encountered an error while processing your request."

    def __call__(self, prompt, **kwargs):
        """Make the model callable directly."""
        return self.generate(prompt, **kwargs)


def get_fallback_model(model_name=None):
    """Factory function to get a properly configured fallback model."""
    model_name = model_name or os.environ.get("FALLBACK_MODEL_NAME")

    # For extremely constrained environments, use an even smaller model
    if os.environ.get("MINIMAL_RESOURCES") == "true":
        logger.info("Using minimal resources mode with distilGPT-2")
        return FallbackModel(model_name="distilgpt2", max_length=512, temperature=0.8)

    # Default fallback model
    return FallbackModel(model_name=model_name)
