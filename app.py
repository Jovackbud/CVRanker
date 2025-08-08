import os
import tempfile
import shutil
import pandas as pd
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io
from typing import List
from weasyprint import HTML, CSS

# Import your processing functions and config
from src.utils import extract_text_from_pdf, calculate_similarities, create_dataframe
from src.summarizer import summarize_cv
from src.gemini_embedding import embed_multiple_documents
from src.config import ALLOWED_EXTENSIONS, DATA_COLUMNS, MAX_FILE_SIZE_MB

import logging

# --- Logging Configuration ---
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.info("Logging configured. Root level set to INFO. Noisy libraries set to WARNING.")

# --- FastAPI App Initialization ---
app = FastAPI(title="CV Ranker API")

# --- Template Configuration ---
# Point to the 'templates' directory
templates = Jinja2Templates(directory="templates")

def allowed_file(filename: str) -> bool:
    """Checks if a file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_upload_form(request: Request):
    """Serves the main upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_and_process(
    request: Request,
    cv_files: List[UploadFile] = File(...),
    jd_file: UploadFile = File(...),
    min_score: int = Form(70), # Note: This is still 70, but upload.html has been updated to 50
    max_results: int = Form(10) # Note: This is still 10, but upload.html has been updated to 3
):
    """
    Handles file upload, processing, filtering, and renders the results page.
    """
    # --- File Validation section ---
    if not jd_file or not jd_file.filename:
        return HTMLResponse(content="<h2>Error: No Job Description file selected.</h2>", status_code=400)
    if not allowed_file(jd_file.filename):
        return HTMLResponse(content="<h2>Error: Invalid file type for Job Description. Only PDFs are allowed.</h2>", status_code=400)
    
    valid_cv_files = [cv for cv in cv_files if cv.filename and allowed_file(cv.filename)]
    if not valid_cv_files:
        return HTMLResponse(content="<h2>Error: No valid CV files were uploaded. Please upload PDF files.</h2>", status_code=400)

    # --- File Size Validation ---
    max_file_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024 # Convert MB to bytes

    if jd_file.size is None or jd_file.size > max_file_size_bytes:
        logger.warning(f"Job Description file size exceeds limit: {jd_file.filename} ({jd_file.size} bytes)")
        return HTMLResponse(content=f"<h2>Error: Job Description file ({jd_file.filename}) exceeds {MAX_FILE_SIZE_MB}MB limit.</h2>", status_code=413) # 413 Payload Too Large
    
    for cv in valid_cv_files:
        if cv.size is None or cv.size > max_file_size_bytes:
            logger.warning(f"CV file size exceeds limit: {cv.filename} ({cv.size} bytes)")
            return HTMLResponse(content=f"<h2>Error: One or more CV files exceed {MAX_FILE_SIZE_MB}MB limit. Please upload smaller files.</h2>", status_code=413)

    # --- Temporary File Handling ---
    temp_dir = None # Initialize temp_dir to None
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory for uploads: {temp_dir}")

        # Save JD file to temp directory
        jd_filepath = os.path.join(temp_dir, jd_file.filename)
        with open(jd_filepath, "wb") as buffer:
            buffer.write(await jd_file.read())
        await jd_file.close() # Close the UploadFile object

        # Save CV files to temp directory
        saved_cv_files = [] # Store paths for processing
        original_filenames = []
        for cv in valid_cv_files:
            cv_filepath = os.path.join(temp_dir, cv.filename)
            with open(cv_filepath, "wb") as buffer:
                buffer.write(await cv.read())
            saved_cv_files.append(cv_filepath)
            original_filenames.append(cv.filename)
            await cv.close() # Close the UploadFile object
        
        logger.info(f"Saved {len(saved_cv_files)} CVs and 1 JD to temporary directory.")

        # --- Processing Steps ---
        logger.info("Starting PDF text extraction for JD.")
        # Now extract text from the saved file paths
        jd_text = extract_text_from_pdf(jd_filepath)
        logger.info("JD text extracted.")

        cv_texts = []
        for cv_filepath in saved_cv_files:
            logger.info(f"Extracting text from CV: {os.path.basename(cv_filepath)}")
            cv_texts.append(extract_text_from_pdf(cv_filepath))
        logger.info(f"Extracted text from {len(cv_texts)} CVs.")

        # Step 3: Get raw summaries from the AI
        logger.info("Generating raw summaries from AI.")
        raw_summaries = [summarize_cv(cv) for cv in cv_texts]
        logger.info("Raw summaries generated.")

        # --- Step 4: Process Summaries ---

        # Step 4a: Extract names and create clean summaries simultaneously
        names = []
        clean_summaries = []
        for summary in raw_summaries:
            parts = summary.split('\n', 1)
            name_part = parts[0]
            # Removing potential markdown characters from the name line for cleaner display
            names.append(name_part.replace('*', '').replace('#', '').strip())
            
            if len(parts) > 1:
                summary_part = parts[1]
                # Clean up whitespace in the summary part
                clean_summaries.append(" ".join(summary_part.split()).strip())
            else:
                clean_summaries.append("") # Handle cases where there's no summary text after name
        logger.info("Names and clean summaries extracted.")

        # Step 4b: Prepare data for HTML display (replace \n with <br />)
        html_display_summaries = []
        for summary_text in raw_summaries:
            # The LLM output is expected to have the name on the first line, followed by summary text.
            # Split at the first newline to separate the name from the summary content.
            parts = summary_text.split('\n', 1)
            
            if len(parts) > 1:
                # parts[1] contains the actual summary text, which might have internal newlines.
                summary_content = parts[1]
                # Replace all newline characters with HTML <br /> tags for display.
                html_summary = summary_content.replace('\n', '<br />')
            else:
                # If there's no newline after the name, just take the whole text and replace newlines
                html_summary = summary_text.replace('\n', '<br />')
                
            html_display_summaries.append(html_summary)
        logger.info("HTML display summaries prepared.")

        # Step 5: Embed documents (using the raw summaries is fine here)
        documents_to_embed = raw_summaries + [jd_text]
        logger.info("Generating embeddings for documents.")
        embeddings = embed_multiple_documents(documents_to_embed)
        logger.info("Embeddings generated.")

        # Step 6: Calculate similarities
        logger.info("Calculating similarities.")
        similarities = calculate_similarities(embeddings)
        logger.info("Similarities calculated.")

        # Step 7: Create the DataFrame with CLEAN summaries for the CSV/JSON
        logger.info("Creating DataFrame.")
        df = create_dataframe(names, original_filenames, clean_summaries, similarities)
        logger.info("DataFrame created.")

        # Step 8: Filter and slice the DataFrame
        logger.info("Filtering and slicing DataFrame.")
        df_filtered = df.copy()
        if not df_filtered.empty:
            score_column_name = DATA_COLUMNS["SCORE"]
            # Ensure the score column is numeric for comparison
            df_filtered[score_column_name] = pd.to_numeric(df_filtered[score_column_name], errors='coerce')
            # Remove any rows where score conversion failed
            df_filtered.dropna(subset=[score_column_name], inplace=True)
            
            df_filtered = df_filtered[df_filtered[score_column_name] >= min_score]
            df_filtered = df_filtered.head(max_results)
            
            # Format score for display after filtering and slicing
            df_filtered[score_column_name] = df_filtered[score_column_name].apply(lambda x: f"{x:.1f}")
        logger.info("DataFrame filtered and sliced.")

        # Step 9: Prepare data for each output format
        results_json = df_filtered.to_json(orient='records')

        df_display = df_filtered.copy()
        
        # Create a mapping from filename to the HTML-ready summary string
        filename_to_html_display_summary = dict(zip(original_filenames, html_display_summaries)) 
        
        summary_col_name = DATA_COLUMNS["SUMMARY"]
        filename_col_name = DATA_COLUMNS["FILENAME"]
        
        if filename_col_name in df_display.columns:
            # Map the generated HTML display summaries into the DataFrame's summary column
            df_display[summary_col_name] = df_display[filename_col_name].map(filename_to_html_display_summary)
        else:
            logger.warning(f"Column '{filename_col_name}' not found in df_display for HTML summary mapping. HTML summaries might not be displayed.")
            # Fallback if the filename column is missing
            df_display[summary_col_name] = ""

        # Convert the DataFrame with proper HTML summaries to an HTML table string.
        # escape=False is crucial here to ensure the <br /> tags are rendered.
        results_html = df_display.to_html(classes='table table-striped', index=False, table_id='results-table', escape=False)
        logger.info("Results prepared for display.")

        # Step 10: Render the results page
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "results_data": results_html,
                "results_json": results_json
            }
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred during upload and processing: {e}", exc_info=True)
        # Return an error response. Consider using the error.html template here.
        # For simplicity, we'll return an HTMLResponse, but ideally it would be a proper template.
        return HTMLResponse(content="<h2>Error: An unexpected error occurred during processing.</h2>", status_code=500)

    finally:
        # Ensure the temporary directory is removed, even if errors occur
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
            logger.info("Temporary directory cleaned up.")
    

@app.post("/download-csv")
async def download_csv(results_json: str = Form(...)):
    """
    Receives results data as a JSON string from a form, converts it to a CSV,
    and streams it back to the user as a file download.
    """
    try:
        # Use pandas to easily convert the JSON string back into a DataFrame
        # The 'orient="records"' must match the format we used to create the JSON
        df = pd.read_json(io.StringIO(results_json), orient='records')

        # Use an in-memory text stream to hold the CSV data
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        
        # Create a response that the browser will interpret as a file download
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cv_ranking_results.csv"}
        )
        return response

    except Exception as e:
        logger.error(f"Error during CSV download: {e}", exc_info=True)
        return HTMLResponse(content="<h2>Error: Could not generate CSV file.</h2>", status_code=500)
    

@app.post("/download-pdf")
async def download_pdf(results_json: str = Form(...)):
    """
    Receives results data as a JSON string, converts it to a styled HTML report,
    renders it as a PDF, and streams it back for download.
    """
    try:
        # Convert the JSON back into a DataFrame
        df = pd.read_json(io.StringIO(results_json), orient='records')

        # Convert the DataFrame to an HTML table
        html_table = df.to_html(index=False, table_id="results-table", escape=False)

        # Create CSS for a professional-looking report
        pdf_css = """
            @page { size: A4 landscape; margin: 1.5cm; }
            body { font-family: sans-serif; }
            h1 { text-align: center; color: #333; }
            #results-table { border-collapse: collapse; width: 100%; font-size: 10px; }
            #results-table th, #results-table td { border: 1px solid #ddd; padding: 6px; }
            #results-table th { background-color: #0d6efd; color: white; padding-top: 10px; padding-bottom: 10px; text-align: left; }
            #results-table tr:nth-child(even) { background-color: #f2f2f2; }
            #results-table td p { margin: 0; }
        """
        
        # Combine everything into a full HTML document string
        full_html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>CV Ranking Results</title></head>
        <body><h1>CV Ranking Results</h1>{html_table}</body></html>
        """

        # Use WeasyPrint to render the HTML and CSS into a PDF in memory
        pdf_bytes = HTML(string=full_html).write_pdf(stylesheets=[CSS(string=pdf_css)])

        # Add a check to ensure pdf_bytes is not None before proceeding.
        if pdf_bytes is None:
            raise ValueError("PDF generation failed, resulted in None.")

        # Create a response that the browser will interpret as a PDF file download
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cv_ranking_results.pdf"}
        )

    except Exception as e:
        logger.error(f"Error during PDF download: {e}", exc_info=True)
        return HTMLResponse(content="<h2>Error: Could not generate PDF file.</h2>", status_code=500)
    

@app.get("/health", status_code=200)
async def health_check():
    """
    Simple endpoint for the hosting platform to verify the app is live and healthy.
    """
    return {"status": "ok"}