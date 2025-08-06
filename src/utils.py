import logging
import pdfplumber
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from .config import DATA_COLUMNS

logger = logging.getLogger(__name__) # Initialize a logger for this module

def extract_text_from_pdf(pdf_stream) -> str:
    """
    Extracts text from a PDF file stream.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        # Log the error with traceback
        logger.error(f"Error extracting text from PDF stream: {e}", exc_info=True)
        return "" # Return empty string on failure

def calculate_similarities(embeddings_list: list) -> list[float]:
    """
    Calculates cosine similarities between CV embeddings and the JD embedding.
    """
    if not embeddings_list or len(embeddings_list) < 2:
        logger.warning("Not enough embeddings to calculate similarities. Need at least 2 (JD + 1 CV).")
        return []
    
    # JD embedding is always the last one
    jd_embedding = np.array(embeddings_list[-1]).reshape(1, -1)
    cv_embeddings = [np.array(cv_emb) for cv_emb in embeddings_list[:-1]]

    similarities = []
    for cv_emb in cv_embeddings:
        try:
            score = cosine_similarity(cv_emb.reshape(1, -1), jd_embedding)[0][0]
            similarities.append(round(score * 100, 2))
        except Exception as e:
            # This shouldn't typically happen with valid embeddings but good for robustness
            logger.error(f"Error calculating cosine similarity for a CV embedding: {e}", exc_info=True)
            similarities.append(0.0) # Append a 0 score for the problematic CV

    return similarities

def create_dataframe(names: list[str], filenames: list[str], summaries: list[str], similarities: list[float]) -> pd.DataFrame:
    """
    Creates a DataFrame with names, filenames, summaries, and similarity scores,
    then sorts it by score.
    """
    # Ensure all lists have the same length to prevent DataFrame creation errors
    min_len = min(len(names), len(filenames), len(summaries), len(similarities))
    if not (len(names) == len(filenames) == len(summaries) == len(similarities)):
        logger.warning(
            f"Mismatched input list lengths for DataFrame creation. "
            f"Truncating to shortest length ({min_len}). "
            f"Names: {len(names)}, Filenames: {len(filenames)}, Summaries: {len(summaries)}, Similarities: {len(similarities)}"
        )
        names = names[:min_len]
        filenames = filenames[:min_len]
        summaries = summaries[:min_len]
        similarities = similarities[:min_len]


    df = pd.DataFrame({
        DATA_COLUMNS["NAME"]: names,
        DATA_COLUMNS["FILENAME"]: filenames,
        DATA_COLUMNS["SUMMARY"]: summaries,
        DATA_COLUMNS["SCORE"]: similarities
    })
    
    # Sort by the score in descending order - Changed to avoid inplace=True for better chaining/immutability
    df = df.sort_values(by=DATA_COLUMNS["SCORE"], ascending=False)
    
    # Format the score for better display
    df[DATA_COLUMNS["SCORE"]] = df[DATA_COLUMNS["SCORE"]].apply(lambda x: f"{x:.1f}")
    
    return df