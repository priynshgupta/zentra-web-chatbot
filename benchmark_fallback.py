"""
Benchmark script for ZentraChatbot fallback model.
This script tests the performance of the fallback model to ensure
it works efficiently within Heroku constraints.
"""

import os
import time
import logging
import psutil
import argparse
from app.fallback_model import get_fallback_model, FallbackModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('benchmark')

def monitor_resources():
    """Monitor memory usage and CPU utilization."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        'memory_mb': memory_info.rss / (1024 * 1024),  # Convert to MB
        'cpu_percent': process.cpu_percent(interval=0.1),
        'threads': len(process.threads())
    }

def benchmark_model(model_name, prompt, iterations=3):
    """Benchmark the fallback model performance."""
    logger.info(f"Benchmarking model: {model_name}")

    # Create the model
    start_time = time.time()
    model = FallbackModel(model_name=model_name)

    # Record initialization metrics
    init_resources = monitor_resources()
    init_time = time.time() - start_time
    logger.info(f"Model initialization time: {init_time:.2f}s")
    logger.info(f"Memory after initialization: {init_resources['memory_mb']:.2f}MB")

    # Generate responses and measure
    generation_times = []
    for i in range(iterations):
        logger.info(f"Running iteration {i+1}/{iterations}")
        start_time = time.time()
        response = model(prompt)
        generation_time = time.time() - start_time
        generation_times.append(generation_time)

        resources = monitor_resources()
        logger.info(f"Generation time: {generation_time:.2f}s")
        logger.info(f"Memory usage: {resources['memory_mb']:.2f}MB")
        logger.info(f"CPU utilization: {resources['cpu_percent']:.1f}%")
        logger.info(f"Response length: {len(response)} chars")
        logger.info(f"Sample: {response[:100]}...\n")

    return {
        'init_time': init_time,
        'init_memory_mb': init_resources['memory_mb'],
        'avg_generation_time': sum(generation_times) / len(generation_times),
        'min_generation_time': min(generation_times),
        'max_generation_time': max(generation_times),
        'final_memory_mb': resources['memory_mb'],
        'final_cpu_percent': resources['cpu_percent']
    }

def main():
    parser = argparse.ArgumentParser(description='Benchmark fallback models')
    parser.add_argument('--model', default='all', choices=['neo-1.3B', 'distilgpt2', 'all'],
                        help='Model to benchmark')
    parser.add_argument('--minimal', action='store_true',
                        help='Use minimal resources mode')
    args = parser.parse_args()

    # Set minimal resources flag if specified
    if args.minimal:
        os.environ["MINIMAL_RESOURCES"] = "true"
        logger.info("Running in minimal resources mode")

    # Define models to test
    models_to_test = []
    if args.model == 'all' or args.model == 'neo-1.3B':
        models_to_test.append(('EleutherAI/gpt-neo-1.3B', 'Standard fallback model'))
    if args.model == 'all' or args.model == 'distilgpt2':
        models_to_test.append(('distilgpt2', 'Minimal resources model'))

    # Define test prompt
    prompt = """
    Explain how a chatbot works in simple terms, and describe some of its applications
    in modern businesses. What are the key components required to build an effective chatbot?
    """

    all_results = {}

    # Run benchmarks for each model
    for model_name, description in models_to_test:
        logger.info(f"========== Testing {description} ({model_name}) ==========")
        try:
            results = benchmark_model(model_name, prompt)
            all_results[model_name] = results

            # Log summary
            logger.info(f"===== {model_name} Summary =====")
            logger.info(f"Initialization time: {results['init_time']:.2f}s")
            logger.info(f"Avg generation time: {results['avg_generation_time']:.2f}s")
            logger.info(f"Memory usage: {results['final_memory_mb']:.2f}MB")
            logger.info("============================\n")

        except Exception as e:
            logger.error(f"Error testing {model_name}: {e}")

    # Compare models if multiple were tested
    if len(all_results) > 1:
        logger.info("======= Model Comparison =======")
        for model_name, results in all_results.items():
            logger.info(f"{model_name}:")
            logger.info(f"  Avg generation time: {results['avg_generation_time']:.2f}s")
            logger.info(f"  Memory usage: {results['final_memory_mb']:.2f}MB")
        logger.info("===============================")

    return all_results

if __name__ == "__main__":
    main()
