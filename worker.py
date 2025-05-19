"""
Worker script for ZentraChatbot fallback model processing.

This script is designed to be run as a separate worker dyno in Heroku to handle
the loading and management of the language model, keeping it in memory and
avoiding repeated loads, which would cause timeout issues.

Usage:
- Deploy as a worker dyno in Heroku:
  web: gunicorn -k eventlet -w 1 main:app
  worker: python worker.py
"""

import os
import sys
import time
import logging
import signal
import redis
from threading import Thread
from queue import Queue, Empty
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('worker')

# Global variables
should_exit = False
generation_queue = Queue()
response_queue = Queue()

def initialize_redis():
    """Initialize Redis connection for message passing"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        return redis.from_url(redis_url)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

def initialize_model():
    """Initialize the appropriate LLM based on environment"""
    try:
        # Check if using minimal resources mode
        if os.environ.get("MINIMAL_RESOURCES") == "true":
            logger.info("Initializing minimal resources mode model")
            from app.fallback_model import get_fallback_model
            model = get_fallback_model()
            logger.info("Minimal resources model initialized: distilgpt2")
        else:
            logger.info("Initializing standard fallback model")
            from app.fallback_model import get_fallback_model
            model = get_fallback_model()
            logger.info("Standard fallback model initialized: EleutherAI/gpt-neo-1.3B")

        return model
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        return None

def model_worker():
    """Worker thread that processes generation requests"""
    global should_exit

    logger.info("Starting model worker thread")
    try:
        # Initialize model once and keep in memory
        model = initialize_model()
        if model is None:
            logger.error("Failed to initialize model, worker exiting")
            return

        logger.info("Model worker ready to process requests")
        while not should_exit:
            try:
                # Get the next prompt with a timeout to allow checking for exit flag
                try:
                    job = generation_queue.get(timeout=1)
                except Empty:
                    continue

                job_id = job.get('id')
                prompt = job.get('prompt')
                logger.info(f"Processing job {job_id}, prompt length: {len(prompt)}")

                # Generate response
                try:
                    start_time = time.time()
                    response = model(prompt)
                    duration = time.time() - start_time
                    logger.info(f"Job {job_id} completed in {duration:.2f}s")

                    # Put the result in the response queue
                    response_queue.put({
                        'id': job_id,
                        'response': response,
                        'success': True,
                        'duration': duration
                    })
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    response_queue.put({
                        'id': job_id,
                        'response': str(e),
                        'success': False
                    })

            except Exception as e:
                logger.error(f"Error in model worker: {e}")

    except Exception as e:
        logger.error(f"Fatal error in model worker: {e}")

def redis_listener(r):
    """Listen for generation requests from Redis"""
    global should_exit

    pubsub = r.pubsub()
    pubsub.subscribe('zentrachatbot:generate')
    logger.info("Redis listener started")

    try:
        for message in pubsub.listen():
            if should_exit:
                break

            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    logger.info(f"Received job {data.get('id')}")
                    generation_queue.put(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message['data']}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
    except Exception as e:
        logger.error(f"Error in Redis listener: {e}")
    finally:
        pubsub.unsubscribe()

def redis_publisher(r):
    """Publish generation results back to Redis"""
    global should_exit

    logger.info("Redis publisher started")
    while not should_exit:
        try:
            try:
                result = response_queue.get(timeout=1)
            except Empty:
                continue

            # Publish the result
            r.publish('zentrachatbot:response', json.dumps(result))
            logger.info(f"Published result for job {result.get('id')}")

        except Exception as e:
            logger.error(f"Error in Redis publisher: {e}")

def signal_handler(sig, frame):
    """Handle termination signals"""
    global should_exit
    logger.info("Shutdown signal received, exiting...")
    should_exit = True

def main():
    """Main worker process"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Redis if in production
    if os.environ.get("HEROKU_APP_NAME"):
        r = initialize_redis()
        if r is None:
            logger.error("Failed to initialize Redis, exiting")
            return 1

        # Start the Redis listener and publisher threads
        Thread(target=redis_listener, args=(r,), daemon=True).start()
        Thread(target=redis_publisher, args=(r,), daemon=True).start()
    else:
        # For local testing, just initialize a model
        logger.info("Running in local mode (no Redis)")
        model = initialize_model()
        if model is None:
            logger.error("Failed to initialize model, exiting")
            return 1

        # Test the model
        prompt = "Hello, can you tell me about ZentraChatbot?"
        logger.info(f"Testing model with prompt: {prompt}")
        response = model(prompt)
        logger.info(f"Model response: {response}")
        return 0

    # Start the model worker thread
    model_thread = Thread(target=model_worker, daemon=True)
    model_thread.start()

    # Keep the main thread alive
    try:
        while not should_exit:
            time.sleep(1)
    except KeyboardInterrupt:
        should_exit = True

    logger.info("Waiting for threads to exit...")
    model_thread.join(timeout=5)
    logger.info("Worker process exited")
    return 0

if __name__ == "__main__":
    sys.exit(main())
