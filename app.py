import os
import pandas as pd
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io
from typing import List
import markdown2
from weasyprint import HTML, CSS

# Import your processing functions and config
from src.utils import extract_text_from_pdf, calculate_similarities, create_dataframe
from src.summarizer import summarize_cv
from src.gemini_embedding import embed_multiple_documents
from src.config import ALLOWED_EXTENSIONS, DATA_COLUMNS, MAX_FILE_SIZE_MB

import logging

# Configure basic logging (adjust for production as needed)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    min_score: int = Form(70),
    max_results: int = Form(10)
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

    try:
        # --- Processing Steps ---
        logger.info("Starting PDF text extraction for JD.")
        jd_text = extract_text_from_pdf(jd_file.file)
        logger.info("JD text extracted.")

        cv_texts = []
        original_filenames = []
        for cv in valid_cv_files:
            logger.info(f"Extracting text from CV: {cv.filename}")
            cv_texts.append(extract_text_from_pdf(cv.file))
            original_filenames.append(cv.filename)
            await cv.close()
        await jd_file.close()
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
            # Split the summary into name and the rest of the text, at most once
            parts = summary.split('\n', 1)
            
            # Extract and clean the name
            name_part = parts[0]
            names.append(name_part.replace('*', '').replace('#', '').strip())
            
            # If there's a summary part after the name, clean it. Otherwise, use an empty string.
            if len(parts) > 1:
                summary_part = parts[1]
                # Replace all newlines in the remaining summary with a space
                clean_summaries.append(" ".join(summary_part.split()).strip())
            else:
                clean_summaries.append("") # Handle cases where there might be no summary after the name
        logger.info("Names and clean summaries extracted.")

        # Step 4b: And create HTML summaries for web/PDF display
        html_summaries = [markdown2.markdown(s, extras=["break-on-newline"]) for s in raw_summaries]
        logger.info("HTML summaries generated.")

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
            score_column_name = DATA_COLUMNS["SCORE"] # Access DATA_COLUMNS from config
            df_filtered[score_column_name] = pd.to_numeric(df_filtered[score_column_name])
            df_filtered = df_filtered[df_filtered[score_column_name] >= min_score]
            df_filtered = df_filtered.head(max_results)
            df_filtered[score_column_name] = df_filtered[score_column_name].apply(lambda x: f"{x:.1f}")
        logger.info("DataFrame filtered and sliced.")

        # Step 9: Prepare data for each output format
        # a) For CSV: JSON from the clean, filtered DataFrame
        results_json = df_filtered.to_json(orient='records')
        
        # b) For Web Page/PDF: Create a display DataFrame and insert the pre-formatted HTML summaries
        df_display = df_filtered.copy()
        # We need to map the HTML summaries to the filtered results. A dictionary is perfect for this.
        # We'll use the filename as a unique key.
        filename_to_html_summary = dict(zip(original_filenames, html_summaries))
        summary_col_name = DATA_COLUMNS["SUMMARY"] # Access DATA_COLUMNS from config
        filename_col_name = DATA_COLUMNS["FILENAME"] # Access DATA_COLUMNS from config
        
        # Ensure the filename_col_name exists in df_display before mapping
        if filename_col_name in df_display.columns:
            df_display[summary_col_name] = df_display[filename_col_name].map(filename_to_html_summary)
        else:
            logger.warning(f"Column '{filename_col_name}' not found in df_display for HTML summary mapping. HTML summaries might not be displayed.")
            # As a fallback, you might want to create an empty summary column or handle this differently
            df_display[summary_col_name] = "" # Or, handle the error as appropriate

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
        # --- UPDATED: Use logger.error for better error handling ---
        logger.error(f"An unexpected error occurred during upload and processing: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "An unexpected error occurred. Please try again or contact support if the issue persists."}, status_code=500)
    

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
            io.BytesIO(pdf_bytes), # Now Pylance knows pdf_bytes can't be None here
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