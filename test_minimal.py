"""
Simple test script for the fallback model.
This script tests only the core functionality without any dependencies.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minimal_test")

def main():
    """Run a minimal test to ensure the fallback architecture works"""
    # Test environment
    logger.info("Testing fallback architecture implementation")    # Test worker client mode - we'll skip actual imports to avoid Redis dependency
    logger.info("Testing worker client architecture")
    try:
        # Check if file exists without importing
        import os.path
        worker_client_path = os.path.join('app', 'worker_client.py')
        if os.path.exists(worker_client_path):
            logger.info(f"✓ Worker client file exists at {worker_client_path}")
        else:
            logger.error(f"✗ Worker client file not found at {worker_client_path}")
            return False
    except Exception as e:
        logger.error(f"✗ Worker client check failed: {e}")
        return False

    # Test basic fallback functionality
    logger.info("Testing basic fallback functionality")
    try:
        # We won't actually initialize the model as it requires downloading
        from app.fallback_model import FallbackModel

        # Just test creating the instance
        model = FallbackModel(model_name=None)
        logger.info(f"✓ Created FallbackModel instance with model_name={model.model_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Fallback model test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("All tests passed! Fallback architecture is properly set up.")
        sys.exit(0)
    else:
        logger.error("Tests failed! Please check the issues above.")
        sys.exit(1)
