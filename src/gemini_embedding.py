# Necessary imports
import os
import google.generativeai as genai
from dotenv import load_dotenv
from src import config

# Load environment variables from .env file (for API key)
load_dotenv()

# Configure the generative AI API key
api_key = os.getenv('google_ai_studio_key')
if not api_key:
    raise ValueError("API key for Gemini not found or empty. Please set the google_ai_studio_key environment variable.")
try:
    genai.configure(api_key=api_key)
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {e}")


def generate_embedding(text, model=config.TEXT_EMBEDDING_MODEL):
    """
    Generates an embedding for the given text using Gemini API.

    Parameters:
    - text (str): The input text to embed.
    - model (str): The model used for generating embeddings.
    - task_type (str): The type of task (e.g., "retrieval_document").
    - title (str): Optional title for the embedding.

    Returns:
    - embedding (list): The embedding vector for the given text.
    """
    try:
        result = genai.embed_content(
            model=model,
            content=text,
        )
        return result['embedding']
    except Exception as e:
        raise RuntimeError(f"Gemini embedding failed for text '{text[:50]}...': {e}")


def embed_multiple_documents(documents, model=config.TEXT_EMBEDDING_MODEL):
    """
    Generates embeddings for a list of documents (e.g., CVs and JD).

    Parameters:
    - documents (list of str): A list of document strings to embed (e.g., CVs, JD).
    - model (str): The model used for generating embeddings.

    Returns:
    - embeddings_list (list of np.array): A list of embeddings where the last item is the JD embedding.
    """
    embeddings_list = []

    for i, doc in enumerate(documents):
        try:
            # Generate embedding for each document
            embedding = generate_embedding(doc, model=model)
            # Append the embedding to the list
            embeddings_list.append(embedding)
        except RuntimeError as e:
            # Propagate the error or handle it (e.g., log and skip)
            # For now, let's propagate it
            raise RuntimeError(f"Failed to embed document {i+1}/{len(documents)} ('{doc[:50]}...'): {e}")
        except Exception as e:
            # Catch any other unexpected errors during embedding for a specific document
            raise RuntimeError(f"Unexpected error embedding document {i+1}/{len(documents)} ('{doc[:50]}...'): {e}")
    return embeddings_list
