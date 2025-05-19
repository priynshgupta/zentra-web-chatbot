"""
Test script to validate the worker-based fallback model.

This script simulates the production environment locally by:
1. Starting a Redis server (if not already running)
2. Starting the worker process
3. Sending test requests via the worker_client interface

Usage:
    python test_worker.py
"""

import os
import sys
import time
import logging
import threading
import subprocess
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_worker')

# Global variables
worker_process = None
redis_process = None

def start_redis():
    """Start a Redis server if not already running"""
    global redis_process

    # Check if Redis is already running
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        logger.info("Redis is already running")
        return True
    except:
        logger.info("Starting Redis server")
        try:
            # Try to start Redis
            redis_process = subprocess.Popen(
                ["redis-server"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Give it time to start

            # Check if it's running
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            logger.info("Redis server started")
            return True
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            logger.error("Please install and start Redis manually")
            return False

def start_worker():
    """Start the worker process"""
    global worker_process

    logger.info("Starting worker process")
    # Set environment variables
    env = os.environ.copy()
    env["HEROKU_APP_NAME"] = "test-app"
    env["REDIS_URL"] = "redis://localhost:6379"

    # Start the worker
    worker_process = subprocess.Popen(
        [sys.executable, "worker.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give worker time to initialize
    time.sleep(5)

    # Check if still running
    if worker_process.poll() is None:
        logger.info("Worker process started")

        # Start a thread to monitor worker output
        def monitor_output():
            while worker_process.poll() is None:
                line = worker_process.stdout.readline()
                if line:
                    logger.info(f"Worker: {line.decode().strip()}")
                time.sleep(0.1)

        threading.Thread(target=monitor_output, daemon=True).start()
        return True
    else:
        stdout, stderr = worker_process.communicate()
        logger.error(f"Worker failed to start: {stderr.decode()}")
        return False

def cleanup():
    """Clean up processes on exit"""
    if worker_process and worker_process.poll() is None:
        logger.info("Terminating worker process")
        worker_process.terminate()
        worker_process.wait(timeout=5)

    if redis_process and redis_process.poll() is None:
        logger.info("Terminating Redis server")
        redis_process.terminate()
        redis_process.wait(timeout=5)

def test_generation():
    """Test the fallback model through the worker client"""
    # Set environment variables for client
    os.environ["HEROKU_APP_NAME"] = "test-app"
    os.environ["REDIS_URL"] = "redis://localhost:6379"

    from app.worker_client import generate_via_worker

    test_prompts = [
        "Hello, how are you today?",
        "Can you explain what ZentraChatbot does?",
        "What are some features of a good chatbot?"
    ]

    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: Sending prompt: {prompt}")

        start_time = time.time()
        response = generate_via_worker(prompt, timeout=60)
        duration = time.time() - start_time

        logger.info(f"Response received in {duration:.2f}s")
        logger.info(f"Response: {response[:100]}...")
        logger.info("-" * 50)
        time.sleep(1)

    return True

def main():
    """Main test function"""
    # Register cleanup handler
    atexit.register(cleanup)

    # Start Redis if needed
    if not start_redis():
        logger.error("Failed to start Redis, exiting")
        return 1

    # Start worker
    if not start_worker():
        logger.error("Failed to start worker, exiting")
        return 1

    # Run test
    logger.info("Running model generation tests")
    success = test_generation()

    if success:
        logger.info("All tests completed successfully")
        return 0
    else:
        logger.error("Tests failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        cleanup()
