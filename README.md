# Project Title: CV Ranker

## Description
A web application that ranks CVs against a job description using AI-powered summarization and semantic similarity.

## Features
-   Upload multiple CVs (PDFs) and one Job Description (PDF).
-   AI-driven CV summarization.
-   Semantic similarity scoring between CVs and JD.
-   Results displayed in a sortable table.
-   Flask-based web interface.
-   Containerized with Docker.

## Setup and Installation
1.  **Clone the repository.**
2.  **Create a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    Create a `.env` file in the project root with the following content:
    ```
    google_ai_studio_key=YOUR_API_KEY
    ```
    Replace `YOUR_API_KEY` with your actual API key for Gemini (Google AI Studio).

## How to Run

### Directly via Flask
1.  Ensure your `.env` file is configured.
2.  Run the application:
    ```bash
    python app.py
    ```
3.  Open your browser to `http://127.0.0.1:5000/`.

### Using Docker
1.  Ensure your `.env` file is configured. The Dockerfile is set up to use it.
2.  Build the Docker image:
    ```bash
    docker build -t cv-ranker .
    ```
3.  Run the Docker container:
    ```bash
    docker run -p 5000:5000 -v $(pwd)/.env:/.env cv-ranker
    ```
    (Or use an absolute path for the `.env` file if preferred).
4.  Open your browser to `http://127.0.0.1:5000/`.

## Project Structure
-   `app.py`: Main Flask application file.
-   `main.py`: Core logic for CV processing and ranking.
-   `src/`: Contains helper modules for PDF processing, text extraction, etc.
-   `dataset/`: Default directory for storing uploaded CVs and JDs.
-   `templates/`: HTML templates for the web interface.
-   `output/`: Directory for storing generated summaries and reports.

## Dependencies
Key dependencies include:
-   Flask
-   Google Generative AI (google-generativeai)
-   scikit-learn
-   pandas

## Future Improvements
-   More robust error handling and user feedback.
-   Advanced configuration options (e.g., model selection, similarity thresholds).
-   Temporary file management for uploaded files.
-   Support for other file formats (e.g., .doc, .docx).
-   User authentication and session management.
-   Asynchronous processing for long-running tasks.
