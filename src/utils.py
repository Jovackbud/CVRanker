# src/utils.py
import pdfplumber
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from .config import DATA_COLUMNS

def extract_text_from_pdf(pdf_stream) -> str:
    """
    Extracts text from a PDF file stream.
    """
    # (No changes in this function)
    text = ""
    try:
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF stream: {e}")
        return ""

def calculate_similarities(embeddings_list: list) -> list[float]:
    """
    Calculates cosine similarities between CV embeddings and the JD embedding.
    """
    # (No changes in this function)
    if not embeddings_list or len(embeddings_list) < 2:
        return []
    
    jd_embedding = np.array(embeddings_list[-1]).reshape(1, -1)
    cv_embeddings = [np.array(cv_emb) for cv_emb in embeddings_list[:-1]]

    similarities = []
    for cv_emb in cv_embeddings:
        score = cosine_similarity(cv_emb.reshape(1, -1), jd_embedding)[0][0]
        similarities.append(round(score * 100, 2))

    return similarities

def create_dataframe(names: list[str], filenames: list[str], summaries: list[str], similarities: list[float]) -> pd.DataFrame:
    """
    Creates a DataFrame with names, filenames, summaries, and similarity scores,
    then sorts it by score.
    """
    df = pd.DataFrame({
        DATA_COLUMNS["NAME"]: names,
        DATA_COLUMNS["FILENAME"]: filenames,
        DATA_COLUMNS["SUMMARY"]: summaries,
        DATA_COLUMNS["SCORE"]: similarities
    })
    # Sort by the score in descending order
    df.sort_values(by=DATA_COLUMNS["SCORE"], ascending=False, inplace=True)
    
    # Format the score for better display
    df[DATA_COLUMNS["SCORE"]] = df[DATA_COLUMNS["SCORE"]].apply(lambda x: f"{x:.1f}")
    
    return df