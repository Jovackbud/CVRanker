# Necessary imports
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file (for API key)
load_dotenv()

# Configure the generative AI API key
api_key = os.getenv('google_ai_studio_key')
genai.configure(api_key=api_key)


def generate_embedding(text, model="models/text-embedding-004"):
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
    result = genai.embed_content(
        model=model,
        content=text,
    )

    return result['embedding']


def embed_multiple_documents(documents, model="models/text-embedding-004"):
    embeddings_dict = {}

    for i, doc in enumerate(documents):
        # Set a title for each document (e.g., "CV1", "CV2", "JD")
        title = f"CV{i + 1}" if i < len(documents) - 1 else "Job Description"
        embedding = generate_embedding(doc, model=model)
        embeddings_dict[title] = embedding

    return embeddings_dict


# Example usage
def main():
    # Example list of CVs and a job description
    cv_texts = [
        "John Doe has extensive experience in software development...",
        "Jane Smith is a data scientist with expertise in machine learning...",
        # Add more CV strings as needed
    ]
    jd_text = "Looking for a software engineer with experience in Python, machine learning, and cloud technologies."

    # Combine CVs and JD into one list
    documents = cv_texts + [jd_text]

    # Generate embeddings
    embeddings = embed_multiple_documents(documents)

    # Output embeddings (trimmed for readability)
    for title, embedding in embeddings.items():
        print(f"{title} embedding: {str(embedding)}]")


if __name__ == "__main__":
    main()
