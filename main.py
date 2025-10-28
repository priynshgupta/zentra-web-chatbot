from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from app.chatbot import get_response, process_website, process_document
import os
from dotenv import load_dotenv
import traceback
from werkzeug.utils import secure_filename
import logging
import hashlib
from app.vector_store import load_vector_store
from app.chatbot import chatbot
import threading
import requests
import atexit
import signal
import sys

# Load environment variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
# CORS will be handled manually via after_request to avoid conflicts

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Add explicit CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Track abort flags by session/user id
global_abort_flags = {}

# Get API settings from environment variables or use defaults
NODE_BACKEND_URL = os.environ.get('NODE_BACKEND_URL', 'http://localhost:4000')

# GPU Status Check Function
def check_gpu_status():
    """Check if GPU is available and Ollama is using it"""
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, check=True)
        gpu_info = result.stdout.strip().split(', ')
        if len(gpu_info) >= 3:
            gpu_name = gpu_info[0]
            memory_used = gpu_info[1]
            memory_total = gpu_info[2]
            logger.info(f"🚀 GPU Detected: {gpu_name}")
            logger.info(f"📊 GPU Memory: {memory_used}MB / {memory_total}MB used")
            return True
    except Exception as e:
        logger.warning(f"⚠️ GPU not detected or nvidia-smi not available: {e}")
        return False

def check_ollama_gpu():
    """Check if Ollama is configured for GPU use"""
    try:
        response = requests.get('http://localhost:11434/api/ps', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                logger.info("🤖 Ollama is running with loaded models")
                for model in models:
                    logger.info(f"   - Model: {model.get('name', 'Unknown')}")
            else:
                logger.info("🤖 Ollama is running but no models loaded")
            return True
    except Exception as e:
        logger.warning(f"⚠️ Ollama not accessible: {e}")
        return False

# Setup for local development
logger.info("🚀 ZentraChatbot starting in GPU-accelerated mode")
gpu_available = check_gpu_status()
ollama_running = check_ollama_gpu()

if gpu_available and ollama_running:
    logger.info("✅ GPU acceleration ready - All text generation will use GPU")
elif gpu_available and not ollama_running:
    logger.warning("⚠️ GPU available but Ollama not running. Start Ollama with: ollama serve")
else:
    logger.warning("⚠️ GPU not available - falling back to CPU (will be slower)")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "ZentraChatbot Flask API",
        "llm": "local_ollama",
        "environment": "development"
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle CORS preflight request - headers handled by after_request
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        query = data.get("query") or data.get("message")
        chat_id = data.get("chatId") or data.get("chat_id")

        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400

        # 1. Fetch website URL for this chatId from Node backend
        website_url = None
        if chat_id:
            try:
                # Forward the Authorization header from the original request
                auth_header = request.headers.get('Authorization')
                headers = {}
                if auth_header:
                    headers['Authorization'] = auth_header

                node_url = f"{NODE_BACKEND_URL}/api/chat/{chat_id}"
                resp = requests.get(node_url, headers=headers)
                if resp.status_code == 200:
                    chat_data = resp.json()
                    website_url = chat_data.get("websiteUrl")
                    logger.info(f"🔍 Retrieved website URL for chat {chat_id}: {website_url}")
                else:
                    logger.warning(f"⚠️ Failed to fetch chat data: {resp.status_code}")
            except Exception as e:
                logger.error(f"❌ Failed to fetch website URL for chat: {e}")
                return jsonify({"success": False, "error": f"Failed to fetch website URL for chat: {e}"}), 500

        # 2. Get the response with website-specific context and session management
        logger.info(f"💬 Generating response for chat {chat_id}, website: {website_url}")
        response = get_response(query, website_url=website_url, chat_id=chat_id)

        # Handle both dict and string responses
        if isinstance(response, dict):
            if response.get('success'):
                return jsonify({"success": True, "response": response.get('response')})
            else:
                return jsonify({"success": False, "error": response.get('error', 'Unknown error')}), 500
        else:
            return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear-session/<chat_id>', methods=['POST'])
def clear_session(chat_id):
    """Clear chat session (optional endpoint for cleanup)"""
    try:
        from app.chatbot import session_manager
        session_manager.clear_session(chat_id)
        return jsonify({"success": True, "message": f"Session cleared for chat {chat_id}"})
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/process-website', methods=['POST'])
def process_website_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        website_url = data.get("websiteUrl") or data.get("website_url")
        if not website_url:
            return jsonify({"success": False, "error": "No website URL provided"}), 400

        if not website_url.startswith(('http://', 'https://')):
            return jsonify({"success": False, "error": "Invalid URL format. URL must start with http:// or https://"}), 400

        sid = request.args.get('sid')
        user_id = sid or 'default'
        global_abort_flags[user_id] = False

        # Pass abort flag to process_website
        def abort_checker():
            return global_abort_flags.get(user_id, False)

        success, result = process_website(website_url, sid=sid, abort_checker=abort_checker)
        if success:
            if isinstance(result, dict):
                message = result["message"]
                categories = result["categories"]
            else:
                message = result
                categories = None

            pages_processed = message.split("Scraped ")[1].split(" pages")[0]
            response = {
                "success": True,
                "message": message,
                "pages_processed": int(pages_processed),
                "website_url": website_url
            }
            if categories:
                response["categories"] = categories
            return jsonify(response)
        else:
            return jsonify({"success": False, "error": result}), 500

    except Exception as e:
        logger.error(f"Error in /process-website: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get-website-categories', methods=['GET'])
def get_website_categories():
    try:
        categories = chatbot.get_website_categories()
        if categories:
            return jsonify({
                "success": True,
                "categories": categories
            })
        else:
            return jsonify({
                "success": False,
                "error": "No website has been processed yet"
            }), 404
    except Exception as e:
        logger.error(f"Error in /get-website-categories: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/upload-document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Get user ID from request
        user_id = request.form.get('userId')
        if not user_id:
            return jsonify({"success": False, "error": "User ID not provided"}), 400

        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the document
        success, message = process_document(filepath)
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 500

    except Exception as e:
        logger.error(f"Error in /upload-document: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/load-website', methods=['POST'])
def load_website():
    try:
        data = request.get_json()
        website_url = data.get("websiteUrl") or data.get("website_url")
        if not website_url:
            return jsonify({"success": False, "error": "No website URL provided"}), 400

        url_hash = hashlib.md5(website_url.encode()).hexdigest()
        collection_name = f"website_{url_hash}"
        vector_store = load_vector_store(collection_name)
        if not vector_store:
            return jsonify({"success": False, "error": "No vector store found for this website"}), 404

        chatbot.vector_store = vector_store
        chatbot.is_initialized = True
        chatbot.website_url = website_url
        chatbot.content_type = "Website"
        return jsonify({"success": True, "message": f"Loaded website: {website_url}"})
    except Exception as e:
        logger.error(f"Error in /load-website: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/abort-processing', methods=['POST'])
def abort_processing():
    user_id = request.json.get('user_id')
    logger.info(f"Abort requested for user_id: {user_id}")
    if user_id:
        global_abort_flags[user_id] = True
        logger.info(f"Abort flag set for user_id: {user_id}")
        return {"success": True, "message": "Abort signal sent."}
    return {"success": False, "message": "No user_id provided."}, 400

# Add a signal handler for clean shutdown
def signal_handler(sig, frame):
    print('\n🛑 CTRL+C detected. Shutting down gracefully...')
    # Kill any lingering processes on port 5000
    try:
        if sys.platform.startswith('win'):
            print('Attempting to kill processes on port 5000...')
            os.system('netstat -ano | findstr :5000 | findstr LISTENING > temp.txt')
            with open('temp.txt', 'r') as f:
                for line in f:
                    columns = line.strip().split()
                    if columns:
                        pid = columns[-1]
                        print(f'Killing process with PID {pid}')
                        os.system(f'taskkill /PID {pid} /F')
            os.remove('temp.txt')
        else:
            # For Unix-based systems
            os.system("lsof -ti:5000 | xargs kill -9")
    except Exception as e:
        print(f"Error during cleanup: {e}")

    print('✅ Flask server shutdown complete')
    sys.exit(0)

# Register the signal handler for SIGINT (CTRL+C)
signal.signal(signal.SIGINT, signal_handler)

# Register a cleanup function to run on normal exit
def cleanup():
    print('Performing final cleanup...')
    # Any additional cleanup code can go here

atexit.register(cleanup)

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        exit(1)
