import os
from . import prompts

import logging # New import
logger = logging.getLogger(__name__) # Initialize a logger for this module
logging.basicConfig(level=logging.INFO) # Set the logging level

# --- API Key Validation (Optional but Recommended) ---
if not os.getenv('GOOGLE_API_KEY'):
    # Log a critical error if the API key is missing. This is a deployment blocker.
    logger.critical(
        "API key 'GOOGLE_API_KEY' not found in environment variables. "
        "Please check your .env file and your deployment environment settings. "
        "Application cannot start without it."
    )
    raise ValueError(
        "API key 'GOOGLE_API_KEY' not found in environment variables. "
        "Please check your .env file and your deployment environment settings."
    )


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
MAX_FILE_SIZE_MB = 20 # Used for both frontend and backend validation

# --- Data Structure Configuration ---
DATA_COLUMNS = {
    "NAME": "Name",
    "FILENAME": "CV Filename",
    "SUMMARY": "Summary",
    "SCORE": "Similarity Score (%)"
}