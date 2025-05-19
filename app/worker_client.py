"""
Redis integration module for fallback model worker communication.
This file provides utilities for the main Flask application to communicate
with the worker process that manages the fallback language model.
"""

import os
import json
import time
import uuid
import logging
import redis
from threading import Lock

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_conn = None
_redis_lock = Lock()

def get_redis_connection():
    """Get a Redis connection, initializing if necessary"""
    global _redis_conn

    if _redis_conn is not None:
        return _redis_conn

    with _redis_lock:
        if _redis_conn is None:
            try:
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
                _redis_conn = redis.from_url(redis_url)
                logger.info("Redis connection initialized")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return None

    return _redis_conn

def generate_via_worker(prompt, timeout=30):
    """
    Send a generation request to the worker via Redis and wait for a response.

    Args:
        prompt (str): The prompt to send to the model
        timeout (int): Maximum time to wait for a response in seconds

    Returns:
        str: The generated response or error message
    """
    # Check if we're in production with Redis
    if not os.environ.get("HEROKU_APP_NAME"):
        # In development, use direct generation
        from app.fallback_model import get_fallback_model
        model = get_fallback_model()
        return model(prompt)

    # Get Redis connection
    r = get_redis_connection()
    if r is None:
        return "Error: Redis connection failed"

    try:
        # Create a unique job ID
        job_id = str(uuid.uuid4())

        # Create pubsub to listen for response
        pubsub = r.pubsub()
        pubsub.subscribe('zentrachatbot:response')

        # Send the generation request
        request_data = {
            'id': job_id,
            'prompt': prompt,
            'timestamp': time.time()
        }
        r.publish('zentrachatbot:generate', json.dumps(request_data))
        logger.info(f"Sent generation request with job ID {job_id}")

        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = pubsub.get_message(timeout=1)
            if message and message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    if data.get('id') == job_id:
                        pubsub.unsubscribe()
                        if data.get('success', False):
                            logger.info(f"Got successful response for job {job_id} in {time.time() - start_time:.2f}s")
                            return data.get('response', '')
                        else:
                            logger.error(f"Error in worker: {data.get('response')}")
                            return f"Error: Model generation failed: {data.get('response')}"
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        # Timeout
        pubsub.unsubscribe()
        logger.error(f"Timeout waiting for response to job {job_id}")
        return "Error: Response generation timed out"

    except Exception as e:
        logger.error(f"Error in generate_via_worker: {e}")
        return f"Error: {str(e)}"
