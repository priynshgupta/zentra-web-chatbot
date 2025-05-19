# Testing the Fallback Mode Implementation

This guide explains how to test the fallback mode implementation before deploying to production.

## Quick Tests

### 1. Test the Fallback Model Directly

Test that the fallback model can be initialized and used:

```bash
python test_simple.py
```

### 2. Run Benchmarks

Benchmark the model to assess memory usage and performance:

```bash
# Standard model
python benchmark_fallback.py

# Minimal resources mode
python benchmark_fallback.py --minimal
```

### 3. Test the Worker Architecture

Test the worker-based architecture (requires Redis):

```bash
python test_worker.py
```

## Local Deployment Testing

### Simulating Heroku Environment

To simulate a Heroku environment locally:

```bash
# Set environment variables
export HEROKU_APP_NAME=test-app
export MINIMAL_RESOURCES=false  # or true for minimal mode

# Start Redis
redis-server &

# Start the worker process
python worker.py &

# Run the Flask app
python main.py
```

### Testing Response Generation

Once the app is running, you can test it:

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How does ZentraChatbot work?", "user_id": "test-user"}'
```

## Production Preparation

Before deploying to Heroku, consider running:

```bash
python heroku_prepare.py --minimal
```

This will:
1. Download and cache the model files
2. Test initialization and generation
3. Report memory usage

## Common Issues and Fixes

### 1. High Memory Usage

If memory usage is too high:

- Enable minimal resources mode: `export MINIMAL_RESOURCES=true`
- Or try a different model: `export FALLBACK_MODEL_NAME=distilgpt2`

### 2. Slow Initial Response

The first response may be slow due to model loading:

- Pre-warm the model in a worker: `python worker.py`
- Make a test request before real usage

### 3. Redis Connection Issues

If Redis connection fails:

- Ensure Redis is running: `redis-cli ping`
- Check connection URL: `echo $REDIS_URL`

### 4. Worker Not Starting

If the worker doesn't start:

- Check dependencies: `pip install -r requirements.txt`
- Look for errors: `python worker.py --debug`

## Monitoring Tools

For production monitoring:

- Memory usage: `heroku ps:scale --app your-app-name`
- Logs: `heroku logs --tail --app your-app-name`
- Health check: `curl https://your-app-name.herokuapp.com/health`
