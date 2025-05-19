# ZentraChatbot Fallback Mode Documentation

This document explains how the ZentraChatbot project implements fallback mode for language model capabilities when deployed to environments without access to the local Llama3 model.

## Overview

ZentraChatbot is designed with flexibility in mind, allowing it to operate in various deployment environments:

1. **Local Development**: Uses Ollama with Llama3 for optimal performance
2. **Cloud Deployment (with API keys)**: Uses OpenAI or Hugging Face APIs
3. **Cloud Deployment (without API keys)**: Uses fallback mode with lightweight models

## Fallback Mode Implementation

The fallback mode activates automatically when deployed to a cloud environment (like Heroku) without API keys for OpenAI or Hugging Face. This ensures that the application can still provide AI responses, albeit potentially at reduced quality compared to the full-featured models.

### Fallback Model Selection

ZentraChatbot implements a tiered approach to model selection:

1. **Primary Model**: EleutherAI/gpt-neo-1.3B (1.3 billion parameters)
   - Good balance of performance and resource usage
   - Works within Heroku eco dyno limits
   - Handles complex queries with reasonable quality

2. **Minimal Resources Mode**: distilgpt2 (82 million parameters)
   - Activated by setting `MINIMAL_RESOURCES=true` environment variable
   - Significantly lower resource usage for constrained environments
   - Suitable for basic chatbot functionality
   - Recommended for free tier Heroku deployments

### Memory Optimization

The fallback implementation includes several optimizations to run efficiently in limited environments:

- **Lazy Loading**: Models are only loaded when first needed
- **Low Memory Mode**: Enabled with `low_cpu_mem_usage=True`
- **Floating Point Optimization**: Uses `float16` precision on GPU environments
- **Memory Management**: Properly releases resources when not in use

### Performance Expectations

Performance varies based on the selected model:

| Model | Memory Usage | Response Time | Quality |
|-------|-------------|--------------|---------|
| EleutherAI/gpt-neo-1.3B | 2-3 GB | 3-8 seconds | Good |
| distilgpt2 | 500-700 MB | 1-3 seconds | Basic |

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FALLBACK_MODEL_NAME` | Custom Hugging Face model identifier | EleutherAI/gpt-neo-1.3B | No |
| `MINIMAL_RESOURCES` | Set to "true" for minimal resources mode | false | No |

### Testing Fallback Mode

You can test the fallback mode locally before deploying:

```bash
# Test standard fallback model
python benchmark_fallback.py --model neo-1.3B

# Test minimal resources mode
python benchmark_fallback.py --model distilgpt2 --minimal
```

### Memory Monitoring

When deployed to Heroku, you should monitor the application's memory usage:

```bash
heroku logs -t --app your-app-name
heroku ps:scale web=1:eco --app your-app-name
```

If you encounter memory issues:

1. Switch to minimal resources mode: `heroku config:set MINIMAL_RESOURCES=true --app your-app-name`
2. Or specify a smaller custom model: `heroku config:set FALLBACK_MODEL_NAME=EleutherAI/gpt-neo-125M --app your-app-name`

## API Endpoint Information

The `/health` endpoint provides information about the current LLM configuration:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "ZentraChatbot Flask API",
  "llm": "fallback",
  "llm_details": {
    "provider": "Hugging Face Transformers",
    "model": "EleutherAI/gpt-neo-1.3B"
  },
  "environment": "production"
}
```

## Troubleshooting

If you encounter issues with the fallback model:

1. Check Heroku logs for errors: `heroku logs --tail --app your-app-name`
2. Verify memory usage: `heroku ps --app your-app-name`
3. Try switching to minimal resources mode if facing memory limitations
4. Ensure the application has time to download the model on first initialization
