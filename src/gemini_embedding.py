import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# Imports for tenacity
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Specific Google API exceptions that are typically retryable
# These are from google-api-core, which underlies langchain-google-genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded, GoogleAPIError

# Import the new config variables
from .config import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__) # Initialize a logger for this module

# Initialize the embedding model once using values from config
embeddings_model = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL_NAME
)

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10), # Exponential backoff: 4s, 8s, 16s, ... up to 10s max
    stop=stop_after_attempt(5), # Try up to 5 times in total (1 initial attempt + 4 retries)
    # Retry on specific Google API errors: Quota Exceeded (429), Internal Server Error (500),
    # Service Unavailable (503), and Deadline Exceeded (timeout)
    retry=retry_if_exception_type((ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded)),
    reraise=True # Re-raise the last exception if all retries fail, to be caught by the outer try-except
)
def _embed_documents_with_retry(documents: list[str]) -> list[list[float]]:
    """
    Internal function to invoke the embedding chain with retries.
    This function will be retried automatically by tenacity on transient errors.
    """
    logger.debug("Attempting to embed documents with GoogleGenerativeAIEmbeddings.")
    embeddings = embeddings_model.embed_documents(documents)
    logger.debug("GoogleGenerativeAIEmbeddings successful.")
    return embeddings

def embed_multiple_documents(documents: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a list of documents using LangChain.
    Handles empty input and API errors with retries.
    """
    if not documents:
        logger.info("No documents provided for embedding. Returning empty list.")
        return []
        
    try:
        # Call the retriable internal function
        return _embed_documents_with_retry(documents)
    except (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
        # This block catches the exception if all retries have failed for known transient API issues.
        logger.error(f"Persistent Google Generative AI API error after retries during embedding: {e}", exc_info=True)
        # Re-raise the exception because embedding failure is critical for the application's core logic.
        # app.py will catch this and display a generic error.
        raise # Re-raise to app.py
    except GoogleAPIError as e: # Catch any other specific Google API errors not covered by retry
        logger.error(f"A non-retryable Google API error occurred during embedding: {e}", exc_info=True)
        raise # Re-raise to app.py
    except Exception as e:
        # This block catches any other unexpected exceptions.
        logger.error(f"An unexpected error occurred during document embedding: {e}", exc_info=True)
        raise # Re-raise to app.py