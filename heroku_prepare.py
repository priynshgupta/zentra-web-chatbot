"""
Heroku-ready test script for the ZentraChatbot fallback mode.

This script will:
1. Download and cache the required model files during build phase
2. Verify the models are properly loaded and functional
3. Ensure optimal memory usage for Heroku's free/eco dynos

Usage:
    python heroku_prepare.py --minimal  # For minimal resources mode
    python heroku_prepare.py            # For standard mode
"""

import os
import sys
import time
import argparse
import logging
import torch
from transformers import pipeline, set_seed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_and_prepare_model(model_name):
    """Download and prepare model for use, caching it for Heroku"""
    start_time = time.time()
    logger.info(f"Preparing model: {model_name}")

    try:
        # Set device
        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Using device: {'CUDA' if device == 0 else 'CPU'}")

        # Initialize model with memory optimization settings
        model_kwargs = {
            "low_cpu_mem_usage": True,
            "torch_dtype": torch.float16 if torch.cuda.is_available() else None
        }

        # Create pipeline
        logger.info("Creating pipeline...")
        generator = pipeline(
            'text-generation',
            model=model_name,
            device=device,
            model_kwargs=model_kwargs
        )

        # Test generation
        logger.info("Testing generation...")
        test_prompt = "Hello, my name is"
        result = generator(
            test_prompt,
            max_length=30,
            do_sample=True,
            temperature=0.7,
            num_return_sequences=1
        )

        end_time = time.time()
        logger.info(f"Model preparation completed in {end_time - start_time:.2f}s")
        logger.info(f"Test output: {result[0]['generated_text']}")

        # Get memory usage
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(f"Memory usage: {memory_mb:.1f}MB")

        return generator

    except Exception as e:
        logger.error(f"Error preparing model: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Prepare fallback model for Heroku deployment')
    parser.add_argument('--minimal', action='store_true', help='Use minimal resources mode')
    parser.add_argument('--preload-only', action='store_true', help='Only preload model without testing')
    args = parser.parse_args()

    # Set random seed for reproducibility
    set_seed(42)

    if args.minimal:
        logger.info("Using MINIMAL RESOURCES MODE")
        model_name = "distilgpt2"
    else:
        logger.info("Using STANDARD MODE")
        model_name = "EleutherAI/gpt-neo-1.3B"

    # Set environment variables to simulate Heroku environment
    os.environ["HEROKU_APP_NAME"] = "zentrachatbot-test"

    if args.minimal:
        os.environ["MINIMAL_RESOURCES"] = "true"

    # Download and prepare model
    generator = download_and_prepare_model(model_name)

    if generator is None:
        logger.error("Failed to prepare model")
        sys.exit(1)

    if not args.preload_only:
        # Run more comprehensive test
        logger.info("Running comprehensive test...")
        test_prompt = """
        Explain how ZentraChatbot works and what makes it special compared to other chatbots.
        What technologies does it use and how does it process information?
        """

        start_time = time.time()
        result = generator(
            test_prompt,
            max_length=200,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        generation_time = time.time() - start_time

        logger.info(f"Generation time: {generation_time:.2f}s")
        logger.info(f"Response length: {len(result[0]['generated_text']) - len(test_prompt)} chars")
        logger.info("Test completed successfully!")

    logger.info("Model preparation completed - ready for Heroku deployment")
    return 0

if __name__ == "__main__":
    sys.exit(main())
