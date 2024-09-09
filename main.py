import os
import glob
from utils import extract_text_from_pdf, vectorize_documents, calculate_similarity, create_dataframe, \
    save_dataframe_to_csv
from summarizer import summarize_cv


def get_cv_files(directory):
    """
    Retrieves all PDF files from the specified directory.
    """
    return glob.glob(os.path.join(directory, '*.pdf'))


def main():
    # Set your directories
    cv_directory = 'dataset/cvs'  # Path to the directory containing CV PDFs
    jd_path = 'dataset/jd'  # Path to the JD PDF

    # Get all CV files from the directory
    cv_files = get_cv_files(cv_directory)

    # Extract text from CVs
    cv_texts = [extract_text_from_pdf(cv_file) for cv_file in cv_files]

    # Extract text from the JD PDF
    jd_text = extract_text_from_pdf(jd_path)

    # Summarize CVs
    cv_summaries = [summarize_cv(cv) for cv in cv_texts]

    # Extract names from summaries
    names = [summary.split('\n')[0].replace("## ", "") for summary in cv_summaries]

    # Vectorize documents and calculate similarity
    X = vectorize_documents(cv_texts, jd_text)
    similarities = calculate_similarity(X)

    # Create and save the DataFrame
    df = create_dataframe(names, cv_summaries, similarities)
    save_dataframe_to_csv(df)


if __name__ == "__main__":
    main()
