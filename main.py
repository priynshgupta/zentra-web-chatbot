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
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Track abort flags by session/user id
global_abort_flags = {}

# Get API settings from environment variables or use defaults
NODE_BACKEND_URL = os.environ.get('NODE_BACKEND_URL', 'http://localhost:4000')

# Check LLM configuration for deployment environments
if os.environ.get('HEROKU_APP_NAME'):
    if not os.environ.get('OPENAI_API_KEY') and not os.environ.get('HUGGINGFACEHUB_API_TOKEN'):
        logger.warning("======================================================================")
        logger.warning("WARNING: No LLM API keys configured for deployment.")
        logger.warning("The application will fall back to a lightweight model which may not")
        logger.warning("perform as well as Llama3. Please configure either OPENAI_API_KEY or")
        logger.warning("HUGGINGFACEHUB_API_TOKEN environment variables for optimal performance.")
        logger.warning("======================================================================")
    else:
        logger.info("LLM API keys configured successfully for deployment.")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Heroku deployment"""
    # Check LLM configuration
    llm_status = "unconfigured"
    llm_details = {}

    if os.environ.get('OPENAI_API_KEY'):
        llm_status = "openai"
        llm_details = {"provider": "OpenAI", "model": "gpt-3.5-turbo"}
    elif os.environ.get('HUGGINGFACEHUB_API_TOKEN'):
        llm_status = "huggingface"
        llm_details = {"provider": "Hugging Face", "model": "Meta-Llama-3-8B-Instruct"}    elif os.environ.get('HEROKU_APP_NAME'):
        # Fallback model in production
        llm_status = "fallback"
        model_name = os.environ.get("FALLBACK_MODEL_NAME", "EleutherAI/gpt-neo-1.3B")
        if os.environ.get("MINIMAL_RESOURCES") == "true":
            model_name = "distilgpt2"

        # Check if worker is active via Redis
        worker_active = False
        if os.environ.get("REDIS_URL"):
            try:
                import redis
                import time

                r = redis.from_url(os.environ.get("REDIS_URL"))
                r.setex("zentrachatbot:health_check", 10, str(time.time()))
                worker_active = True
            except:
                worker_active = False

        llm_details = {
            "provider": "Hugging Face Transformers",
            "model": model_name,
            "worker_active": worker_active
        }
    else:
        llm_status = "local_llama3"
        llm_details = {"provider": "Ollama", "model": "llama3"}

    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "ZentraChatbot Flask API",
        "llm": llm_status,
        "llm_details": llm_details,
        "environment": "production" if os.environ.get('HEROKU_APP_NAME') else "development"
    })

@app.route('/chat', methods=['POST'])
def chat():
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
                node_url = f"{NODE_BACKEND_URL}/api/chat/{chat_id}"
                resp = requests.get(node_url)
                if resp.status_code == 200:
                    website_url = resp.json().get("websiteUrl")
            except Exception as e:
                return jsonify({"success": False, "error": f"Failed to fetch website URL for chat: {e}"}), 500

        # 2. If website_url is found and chatbot is not initialized for it, process it
        if website_url:
            if not chatbot.is_initialized or chatbot.website_url != website_url:
                success, msg = chatbot.process_website(website_url)
                if not success:
                    return jsonify({"success": False, "error": f"Failed to process website: {msg}"}), 500

        # 3. Get the response as usual
        response = get_response(query)
        return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        logger.error(traceback.format_exc())
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
