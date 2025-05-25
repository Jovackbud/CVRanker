import os

# Gemini Model Names
TEXT_EMBEDDING_MODEL = "models/text-embedding-004"
SUMMARY_GENERATION_MODEL = "gemini-1.5-flash"

# Output path (relative to project root)
OUTPUT_DIR = "output"
OUTPUT_CSV_FILENAME = "output.csv"
# derived:
DEFAULT_OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)

# Dataset paths (relative to project root) - for standalone main.py
DEFAULT_CV_DIR = 'dataset/cvs'
DEFAULT_JD_DIR = 'dataset/jd'
