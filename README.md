# CV Ranker

A sophisticated web application that leverages AI to semantically rank candidates based on their CVs against a job description. It automates the initial screening process by providing similarity scores, concise summaries, and downloadable reports, all while being optimized for efficient deployment.

## Key Features

*   **AI-Powered Candidate Matching:** Utilizes semantic understanding to match CVs with job descriptions, going beyond simple keyword matching.
*   **Intelligent Summarization:** Generates concise, two-paragraph summaries of candidate skills and experiences.
*   **PDF Document Processing:** Extracts text seamlessly from both CVs and Job Descriptions in PDF format.
*   **User-Friendly Web Interface:** A clean and intuitive interface for uploading files and viewing results.
*   **Configurable Filtering:** Allows users to set a minimum similarity score and the maximum number of results to display.
*   **Downloadable Reports:** Exports ranked candidate data in CSV and professionally formatted PDF reports.
*   **Robust Error Handling:** Gracefully handles file type, size, and processing errors.
*   **Optimized Performance:** Designed for efficient operation, even on resource-constrained environments.

## Technologies Used

*   **Backend Framework:** FastAPI
*   **Web Server:** Uvicorn
*   **AI/ML:**
    *   LangChain for AI orchestration.
    *   Google Generative AI (Gemini models for summarization and embeddings).
    *   `models/text-embedding-004` for semantic embeddings.
    *   `gemini-2.5-flash-lite` for text generation.
*   **PDF Processing:**
    *   `pdfplumber` for text extraction.
    *   `weasyprint` for PDF report generation.
*   **Data Handling:**
    *   `pandas` for data manipulation and table creation.
    *   `scikit-learn` for cosine similarity calculations.
*   **Frontend:**
    *   HTML, CSS
    *   Bootstrap 5 for styling and components.
*   **Deployment:**
    *   Docker
    *   DigitalOcean App Platform

## Getting Started

### Prerequisites

*   Python 3.10+
*   Pip package installer
*   A Google Cloud Project with the Generative AI API enabled and an API key.
*   **For Linux users (Ubuntu/Debian):** Install system dependencies for `weasyprint`:
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-dev python3-pip python3-venv build-essential \
                          libpango-1.0-0 libpango1.0-dev libcairo2 libcairo2-dev \
                          libgdk-pixbuf2.0-0 libgdk-pixbuf2.0-dev libxml2 libxml2-dev \
                          libxslt1-dev
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Jovackbud/CVRanker.git
    cd CVRanker
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  Create a `.env` file in the root directory of the project (or set environment variables directly in your deployment environment).
2.  Add your Google API Key:
    ```dotenv
    GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
    ```
    *(Replace `YOUR_GOOGLE_API_KEY` with your actual API key)*

### Running the Application

You can run the FastAPI application using Uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The application will be accessible at `http://localhost:8000`.

## Live Demo

Experience the application in action!

[Try the CV Ranker Live](https://cvranker-imcyx.ondigitalocean.app/)

## Usage

1.  Navigate to the application's web page in your browser.
2.  Upload your **Job Description PDF** in the designated field.
3.  Upload one or more **CV PDF files** for the candidates you want to evaluate.
4.  Optionally, adjust the **"Minimum Score (%)"** and **"Max Candidates"** filters.
5.  Click the "Analyze and Rank" button.
6.  View the ranked list of candidates directly on the web page.
7.  Download the results in CSV or PDF format for further analysis or reporting.

## File Structure

.
├── templates/
│   ├── upload.html         # Main upload page
│   ├── results.html        # Page displaying ranking results
│   └── error.html          # Page for displaying errors
├── src/
│   ├── __init__.py
│   ├── config.py           # Application configuration and constants
│   ├── gemini_embedding.py # Handles document embedding using Google AI
│   ├── prompts.py          # Stores AI prompt templates
│   ├── summarizer.py       # Handles CV summarization with AI
│   └── utils.py            # Utility functions (PDF extraction, similarity calculation, etc.)
├── app.py                  # Main FastAPI application file
├── requirements.txt        # Project dependencies
├── .gitignore              # Specifies intentionally untracked files
└── Dockerfile              # Docker configuration for building the image (if used for deployment)

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
