import pdfplumber
import numpy as np
import os
import glob
import pandas as pd
from src import config


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''.join(page.extract_text() for page in pdf.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def vectorize_documents(cv_texts, jd_text):
    """
    Vectorizes the CV texts and the job description using TF-IDF.
    """
    documents = [jd_text] + cv_texts
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(documents)
def create_dataframe(names, summaries, similarities):
    """
    Creates a DataFrame with names, summaries, and similarity scores.
    """
    df = pd.DataFrame({
        'Name': names,
        'Summary': summaries,
        'Score (%)': similarities
    })
    df.sort_values(by='Score (%)', ascending=False, inplace=True)
    return df


def save_dataframe_to_csv(df, output_path=os.path.join(config.OUTPUT_DIR, config.OUTPUT_CSV_FILENAME)):
    """
    Saves the DataFrame to a CSV file.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)


def get_cv_files(directory):
    """
    Retrieves all PDF files from the specified directory.
    """
    return glob.glob(os.path.join(directory, '*.pdf'))


def get_jd_file(jd_directory):
    """
    Retrieves the single PDF file from the specified JD directory.
    Throws an error if there are zero or more than one PDF file.
    """
    jd_files = glob.glob(os.path.join(jd_directory, '*.pdf'))
    if len(jd_files) != 1:
        raise ValueError(f"Expected exactly one JD PDF file in {jd_directory}, but found {len(jd_files)}.")
    return jd_files[0]