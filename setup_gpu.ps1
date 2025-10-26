# GPU Optimization Script for ZentraChatbot (Windows PowerShell)
# This script configures Ollama for optimal GPU performance on RTX 4050

Write-Host "🚀 Optimizing ZentraChatbot for GPU acceleration..." -ForegroundColor Green

# Set environment variables for GPU optimization
$env:OLLAMA_NUM_GPU = "1"  # Use 1 GPU (RTX 4050)
$env:OLLAMA_NUM_PARALLEL = "1"  # Process one request at a time for better GPU utilization
$env:OLLAMA_MAX_LOADED_MODELS = "2"  # Keep up to 2 models in VRAM
$env:OLLAMA_FLASH_ATTENTION = "1"  # Enable Flash Attention for faster inference
$env:OLLAMA_KV_CACHE_TYPE = "f16"  # Use float16 for KV cache to save VRAM
$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:OLLAMA_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"

Write-Host "📊 GPU Configuration:" -ForegroundColor Cyan
Write-Host "   - GPUs to use: $($env:OLLAMA_NUM_GPU)"
Write-Host "   - Parallel requests: $($env:OLLAMA_NUM_PARALLEL)"
Write-Host "   - Max loaded models: $($env:OLLAMA_MAX_LOADED_MODELS)"
Write-Host "   - Flash Attention: $($env:OLLAMA_FLASH_ATTENTION)"

# Check if Ollama is running
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($null -eq $ollamaProcess) {
    Write-Host "🔄 Starting Ollama server with GPU optimization..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 3
} else {
    Write-Host "✅ Ollama server is already running" -ForegroundColor Green
}

# Verify GPU detection
Write-Host "🔍 Checking GPU status..." -ForegroundColor Cyan
try {
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
} catch {
    Write-Host "⚠️ nvidia-smi not found - ensure NVIDIA drivers are installed" -ForegroundColor Red
}

# Verify Llama3 model is available
Write-Host "🤖 Verifying Llama3 model..." -ForegroundColor Cyan
$models = ollama list
if ($models -like "*llama3*") {
    Write-Host "✅ Llama3 model is available" -ForegroundColor Green
} else {
    Write-Host "📥 Downloading Llama3 model for GPU use..." -ForegroundColor Yellow
    ollama pull llama3
}

# Test GPU inference
Write-Host "🧪 Testing GPU inference..." -ForegroundColor Cyan
$testPayload = @{
    model = "llama3"
    prompt = "Hello! Test GPU inference."
    options = @{
        num_gpu = -1
        temperature = 0.7
    }
    stream = $false
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $testPayload -ContentType "application/json"
    Write-Host "✅ GPU inference test successful!" -ForegroundColor Green
    Write-Host "Response: $($response.response.Substring(0, [Math]::Min(100, $response.response.Length)))..." -ForegroundColor White
} catch {
    Write-Host "⚠️ GPU inference test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 GPU optimization complete!" -ForegroundColor Green
Write-Host "💡 Tips for optimal performance:" -ForegroundColor Cyan
Write-Host "   - Keep model conversations under 4K tokens for best speed"
Write-Host "   - Monitor GPU memory usage with: nvidia-smi"
Write-Host "   - Your RTX 4050 has 6GB VRAM - perfect for Llama3-8B"
Write-Host ""
Write-Host "🚀 Start your ZentraChatbot now with GPU acceleration!" -ForegroundColor Green

# Keep environment variables for current session
Write-Host "💾 Environment variables set for current session" -ForegroundColor Yellow
Write-Host "To make permanent, add them to your system environment variables" -ForegroundColor Yellow