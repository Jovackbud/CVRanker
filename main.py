from src.utils import extract_text_from_pdf, create_dataframe, \
    save_dataframe_to_csv, get_cv_files, get_jd_file
from src.summarizer import summarize_cv
from src.gemini_embedding import embed_multiple_documents, generate_embedding
import os # Added for os.path.exists and os.listdir in __main__
from src import config # Import the configuration

def main(cv_dir_path, jd_dir_path):
    # Use the provided directory paths
    cv_directory = cv_dir_path
    jd_directory = jd_dir_path

    # Get all CV files from the directory
    cv_files = get_cv_files(cv_directory)

    # Check if any CVs were found
    if not cv_files:
        print("No CVs found in the directory. Skipping processing.")
        # Optionally, create an empty output file or a file with a message
        # For now, just return
        return

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
    # Pass the filename to summarize_cv for fallback name extraction
    cv_summaries_data = [summarize_cv(cv_text, filename=cv_file.split('/')[-1]) for cv_text, cv_file in zip(cv_texts, cv_files)]

    # Extract names and actual summaries from the list of dictionaries
    names = [summary_dict.get('applicant_name', cv_file.split('/')[-1]) for summary_dict, cv_file in zip(cv_summaries_data, cv_files)]
    actual_summaries = [summary_dict.get('summary', 'Summary not available.') for summary_dict in cv_summaries_data]

    # embed CVS & JD using actual_summaries
    document = actual_summaries + [jd_text]
    embeddings = embed_multiple_documents(document)

    # calculate similarities
    # similarities = calculate_similarities(embeddings) # This line will be removed as the function is removed

    # Create and save the DataFrame
    # df = create_dataframe(names, actual_summaries, similarities) # This line will be modified or removed
    # Placeholder for now, as the actual logic for similarity calculation and dataframe creation will change
    df = create_dataframe(names, actual_summaries, [0.0] * len(names)) # Create df with dummy scores
    save_dataframe_to_csv(df)


if __name__ == "__main__":
    # Use directory paths from config for standalone execution
    cv_dir = config.DEFAULT_CV_DIR
    jd_dir = config.DEFAULT_JD_DIR
    
    # Check if default directories exist and are not empty
    if not os.path.exists(cv_dir) or not os.listdir(cv_dir):
        print(f"Warning: Default CV directory {cv_dir} is empty or does not exist.")
        # Decide if to proceed; for now, we'll still call main but it might fail or do nothing.
    if not os.path.exists(jd_dir) or not os.listdir(jd_dir):
        print(f"Warning: Default JD directory {jd_dir} is empty or does not exist.")
        # Optionally, exit or prevent main() call if JD is essential for standalone run
        # For instance, one might choose to exit if the JD is missing:
        # print("Error: Default JD directory is missing. Cannot run in standalone mode.")
        # exit(1) # Or handle more gracefully

    print(f"Running in standalone mode using CVs from: {cv_dir} and JD from: {jd_dir}")
    main(cv_dir, jd_dir)
    print("DONE")
