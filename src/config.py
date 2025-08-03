import os
from dotenv import load_dotenv
from pydantic.types import SecretStr
from . import prompts

# --- Load Environment Variables ---
load_dotenv()

# --- API Keys ---
# Get the key from the environment
google_api_key_str = os.getenv('google_ai_studio_key')

# Check if the key exists
if not google_api_key_str:
    raise ValueError("API key 'google_ai_studio_key' not found in environment variables. Please check your .env file.")

# Convert the plain string to a SecretStr for security
GOOGLE_API_KEY: SecretStr = SecretStr(google_api_key_str) 

# --- Model Configuration ---
LLM_MODEL_NAME = "gemini-2.5-flash-lite"
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

# --- Prompt Configuration ---
SUMMARIZER_PROMPT_MESSAGES = [
    ("system", prompts.SUMMARIZER_SYSTEM_PROMPT),
    ("user", prompts.SUMMARIZER_USER_PROMPT)
]

# --- Application & UI Configuration ---
ALLOWED_EXTENSIONS = {'pdf'}

# --- Data Structure Configuration ---
DATA_COLUMNS = {
    "NAME": "Name",
    "FILENAME": "CV Filename",
    "SUMMARY": "Summary",
    "SCORE": "Similarity Score (%)"
}