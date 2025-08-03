# src/summarizer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# Import the fully configured variables from our config file
from .config import GOOGLE_API_KEY, LLM_MODEL_NAME, SUMMARIZER_PROMPT_MESSAGES

# 1. Initialize the Language Model using values from config
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL_NAME,
    google_api_key=GOOGLE_API_KEY
)

# 2. Create the prompt template directly from the config
prompt_template = ChatPromptTemplate.from_messages(
    SUMMARIZER_PROMPT_MESSAGES  # <-- This is much cleaner
)

# 3. Create the summarization chain
output_parser = StrOutputParser()
summarization_chain = prompt_template | llm | output_parser


def summarize_cv(cv_text: str) -> str:
    """
    Summarizes the skills and experiences in a CV using a LangChain chain.
    """
    try:
        response = summarization_chain.invoke({"cv_text": cv_text})
        return response
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Error: Could not generate summary."