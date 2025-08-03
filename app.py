import os
import pandas as pd
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io
from typing import List
import markdown2

# Import your processing functions and config
from src.utils import extract_text_from_pdf, calculate_similarities, create_dataframe
from src.summarizer import summarize_cv
from src.gemini_embedding import embed_multiple_documents
from src.config import ALLOWED_EXTENSIONS, DATA_COLUMNS

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
    This is the main workflow for the web app.
    """
    # ... (File Validation section remains the same) ...
    if not jd_file or not jd_file.filename:
        return HTMLResponse(content="<h2>Error: No Job Description file selected.</h2>", status_code=400)
    if not allowed_file(jd_file.filename):
        return HTMLResponse(content="<h2>Error: Invalid file type for Job Description. Only PDFs are allowed.</h2>", status_code=400)

    valid_cv_files = [cv for cv in cv_files if cv.filename and allowed_file(cv.filename)]
    if not valid_cv_files:
        return HTMLResponse(content="<h2>Error: No valid CV files were uploaded. Please upload PDF files.</h2>", status_code=400)

    try:
        # --- Steps 1-6 remain mostly the same ---
        jd_text = extract_text_from_pdf(jd_file.file)

        cv_texts = []
        original_filenames = []
        for cv in valid_cv_files:
            cv_texts.append(extract_text_from_pdf(cv.file))
            original_filenames.append(cv.filename)
            await cv.close()
        await jd_file.close()

        cv_summaries = [summarize_cv(cv) for cv in cv_texts]

        names = []
        for i, summary in enumerate(cv_summaries):
            first_line = summary.split('\n')[0]
            if first_line.startswith("## "):
                names.append(first_line[3:].strip())
            else:
                names.append(first_line.replace('*', '').strip())

        documents_to_embed = cv_summaries + [jd_text]
        embeddings = embed_multiple_documents(documents_to_embed)
        similarities = calculate_similarities(embeddings)

        # --- LOGIC CHANGE STARTS HERE ---

        # 7. Create DataFrame with CLEAN, RAW-TEXT summaries.
        # This DataFrame will be used for the CSV export.
        df = create_dataframe(names, original_filenames, cv_summaries, similarities)

        # 8. Filter and slice the DataFrame based on user options
        df_filtered = df.copy() # Work on a copy to preserve the original df
        if not df_filtered.empty:
            score_column_name = DATA_COLUMNS["SCORE"]
            df_filtered[score_column_name] = pd.to_numeric(df_filtered[score_column_name])
            df_filtered = df_filtered[df_filtered[score_column_name] >= min_score]
            df_filtered = df_filtered.head(max_results)
            df_filtered[score_column_name] = df_filtered[score_column_name].apply(lambda x: f"{x:.1f}")

        # 9. Prepare the data for each specific output format
        
        # a) For the CSV: Create JSON from the CLEAN, filtered DataFrame
        results_json = df_filtered.to_json(orient='records')
        
        # b) For the Web Page: Create a new DataFrame for display,
        #    and convert its 'Summary' column to HTML.
        df_display = df_filtered.copy()
        summary_col_name = DATA_COLUMNS["SUMMARY"]
        df_display[summary_col_name] = df_display[summary_col_name].apply(
            lambda summary: markdown2.markdown(summary, extras=["break-on-newline"])
        )
        
        results_html = df_display.to_html(classes='table table-striped', index=False, table_id='results-table', escape=False)

        # 10. Render the results page with both clean JSON and HTML data
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "results_data": results_html,
                "results_json": results_json
            }
        )

    except Exception as e:
        # ... (Error handling remains the same) ...
        print(f"An unexpected error occurred: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "An unexpected error occurred..."}, status_code=500)
    

@app.post("/download")
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
        print(f"Error during CSV download: {e}")
        return HTMLResponse(content="<h2>Error: Could not generate CSV file.</h2>", status_code=500)