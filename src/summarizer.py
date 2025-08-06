import logging
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .config import LLM_MODEL_NAME, SUMMARIZER_PROMPT_MESSAGES

# Imports for tenacity
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
# Specific Google API exceptions that are typically retryable
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Language Model using values from config
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL_NAME
)

# Create the prompt template directly from the config
prompt_template = ChatPromptTemplate.from_messages(
    SUMMARIZER_PROMPT_MESSAGES
)

# Create the summarization chain
output_parser = StrOutputParser()
summarization_chain = prompt_template | llm | output_parser


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10), # Exponential backoff: 4s, 8s, 16s, ... up to 10s max
    stop=stop_after_attempt(5), # Try up to 5 times in total (1 initial attempt + 4 retries)
    # Retry on specific Google API errors: Quota Exceeded (429), Internal Server Error (500),
    # Service Unavailable (503), and Deadline Exceeded (timeout)
    retry=retry_if_exception_type((ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded)),
    reraise=True # Re-raise the last exception if all retries fail, to be caught by the outer try-except
)
def _summarize_cv_with_retry(cv_text: str) -> str:
    """
    Internal function to invoke the summarization chain with retries.
    This function will be retried automatically by tenacity on transient errors.
    """
    logger.debug("Attempting to summarize CV with AI.")
    response = summarization_chain.invoke({"cv_text": cv_text})
    logger.debug("AI summarization successful.")
    return response


def summarize_cv(cv_text: str) -> str:
    """
    Summarizes the skills and experiences in a CV using a LangChain chain.
    Returns the raw summary from the model. Handles empty input and API errors.
    """
    if not cv_text or not cv_text.strip():
        logger.warning("Received empty or whitespace-only CV text for summarization.")
        return "No content provided for summary."

    try:
        # Call the retriable internal function
        response = _summarize_cv_with_retry(cv_text)
        return response
    except (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
        # This block catches the exception if all retries have failed for a known API issue.
        logger.error(f"Persistent Google Generative AI API error after retries during summarization: {e}", exc_info=True)
        return "Error: Could not generate summary due to persistent API issues (e.g., quota, server error, timeout). Please try again later."
    except Exception as e:
        # This block catches any other unexpected exceptions.
        logger.error(f"An unexpected error occurred during summarization: {e}", exc_info=True)
        return "Error: An unexpected issue occurred during summary generation."