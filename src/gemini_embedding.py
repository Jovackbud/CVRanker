# src/gemini_embedding.py
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# Import the new config variables
from .config import GOOGLE_API_KEY, EMBEDDING_MODEL_NAME

# Initialize the embedding model once using values from config
embeddings_model = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL_NAME, # <-- Change is here
    google_api_key=GOOGLE_API_KEY
)

def embed_multiple_documents(documents: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a list of documents using LangChain.
    """
    try:
        return embeddings_model.embed_documents(documents)
    except Exception as e:
        print(f"Error during document embedding: {e}")
        raise e