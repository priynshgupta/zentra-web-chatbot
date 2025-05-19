import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Tokens for LLMs
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Vector Store Configuration
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "vector_store")

# Model Configuration
MODEL_CONFIG = {
    "model_name": "EleutherAI/gpt-neo-2.7B",
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 50,
    "repetition_penalty": 1.1,
    "no_repeat_ngram_size": 3,
    "early_stopping": True
}

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "zentra_chat")
MONGO_COLLECTIONS = {
    "chats": "chats",
    "user_chats": "user_chats",
    "users": "users"
}
