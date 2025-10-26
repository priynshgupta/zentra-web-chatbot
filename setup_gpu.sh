#!/bin/bash
# GPU Optimization Script for ZentraChatbot
# This script configures Ollama for optimal GPU performance on RTX 4050

echo "🚀 Optimizing ZentraChatbot for GPU acceleration..."

# Set environment variables for GPU optimization
export OLLAMA_NUM_GPU=1  # Use 1 GPU (RTX 4050)
export OLLAMA_NUM_PARALLEL=1  # Process one request at a time for better GPU utilization
export OLLAMA_MAX_LOADED_MODELS=2  # Keep up to 2 models in VRAM
export OLLAMA_FLASH_ATTENTION=1  # Enable Flash Attention for faster inference
export OLLAMA_KV_CACHE_TYPE="f16"  # Use float16 for KV cache to save VRAM
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

echo "📊 GPU Configuration:"
echo "   - GPUs to use: $OLLAMA_NUM_GPU"
echo "   - Parallel requests: $OLLAMA_NUM_PARALLEL"
echo "   - Max loaded models: $OLLAMA_MAX_LOADED_MODELS"
echo "   - Flash Attention: $OLLAMA_FLASH_ATTENTION"

# Check if Ollama is running
if ! pgrep -f "ollama" > /dev/null; then
    echo "🔄 Starting Ollama server with GPU optimization..."
    ollama serve &
    sleep 3
else
    echo "✅ Ollama server is already running"
fi

# Verify GPU detection
echo "🔍 Checking GPU status..."
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader

# Pull or verify Llama3 model is available
echo "🤖 Verifying Llama3 model..."
if ollama list | grep -q "llama3"; then
    echo "✅ Llama3 model is available"
else
    echo "📥 Downloading Llama3 model for GPU use..."
    ollama pull llama3
fi

# Test GPU inference
echo "🧪 Testing GPU inference..."
echo "Generating a test response..."
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Hello! Test GPU inference.",
    "options": {
      "num_gpu": -1,
      "temperature": 0.7
    },
    "stream": false
  }' | jq -r '.response' 2>/dev/null || echo "Test completed (response parsing requires jq)"

echo ""
echo "🎉 GPU optimization complete!"
echo "💡 Tips for optimal performance:"
echo "   - Keep model conversations under 4K tokens for best speed"
echo "   - Monitor GPU memory usage with: watch nvidia-smi"
echo "   - Your RTX 4050 has 6GB VRAM - perfect for Llama3-8B"
echo ""
echo "🚀 Start your ZentraChatbot now with GPU acceleration!"