from src.utils import extract_text_from_pdf, calculate_similarity, create_dataframe, \
    save_dataframe_to_csv, get_cv_files, get_jd_file
from src.summarizer import summarize_cv, document_embedding
from src.gemini_embedding import embed_multiple_documents


def main():
    # Set your directories
    cv_directory = 'dataset/cvs'  # Path to the directory containing CV PDFs
    jd_directory = 'dataset/jd'  # Path to the directory containing the JD PDF

    # Get all CV files from the directory
    cv_files = get_cv_files(cv_directory)

    # Extract text from CVs
    cv_texts = [extract_text_from_pdf(cv_file) for cv_file in cv_files]

    # Get JD file and extract text
    try:
        jd_path = get_jd_file(jd_directory)
        jd_text = extract_text_from_pdf(jd_path)
    except Exception as e:
        print(f"Error extracting text from JD in {jd_directory}: {e}")
        return  # Exit if JD extraction fails

    # Summarize CVs
    cv_summaries = [summarize_cv(cv) for cv in cv_texts]

    # Extract names from summaries
    names = [summary.split('\n')[0].replace("## ", "") for summary in cv_summaries]
    summary_dict = dict(zip(names, cv_summaries))

    # embed CVS & JD
    cv_embeddings = document_embedding(summary_dict.values())
    cv_embeddings_dict = dict(zip(names, cv_embeddings))
    jd_embeddings = document_embedding(jd_text)

    # calculate similarities
    similarities = calculate_similarity(cv_embeddings_dict.values(), jd_embeddings)

    # Create and save the DataFrame
    df = create_dataframe(names, cv_summaries, similarities)
    save_dataframe_to_csv(df)


if __name__ == "__main__":
    main()
    print("DONE")
