from flask import Flask, request, render_template, redirect, url_for
import os
import pandas as pd  # Import pandas to handle CSV files
from werkzeug.utils import secure_filename
from main import main as process_files
import tempfile
import shutil
from src import config

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
# CV_FOLDER and JD_FOLDER are no longer used for request-based uploads
# app.config['CV_FOLDER'] = CV_FOLDER
# app.config['JD_FOLDER'] = JD_FOLDER


# Helper function to check if file is PDF
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_files():
    return render_template('upload.html')  # Create an upload.html page


@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the files
    if 'cv_files' not in request.files or 'jd_file' not in request.files:
        return 'No file part', 400 # Consider a user-friendly error page

    cv_files = request.files.getlist('cv_files')
    jd_file = request.files['jd_file']

    # Validate files
    if not cv_files or not jd_file or jd_file.filename == '':
        return render_template('results.html', error_message="No CV files or JD file selected.")
    if not allowed_file(jd_file.filename) or not all(allowed_file(f.filename) for f in cv_files if f.filename != ''):
        return render_template('results.html', error_message="Invalid file type. Only PDFs are allowed.")
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        temp_cv_folder = os.path.join(temp_dir, 'cvs')
        temp_jd_folder = os.path.join(temp_dir, 'jd')
        os.makedirs(temp_cv_folder, exist_ok=True)
        os.makedirs(temp_jd_folder, exist_ok=True)

        # Save CV files to temp_cv_folder
        for file in cv_files:
            if file and file.filename != '': # Ensure file exists and has a name
                filename = secure_filename(file.filename)
                file.save(os.path.join(temp_cv_folder, filename))

        # Save JD file to temp_jd_folder
        jd_filename = secure_filename(jd_file.filename)
        jd_file.save(os.path.join(temp_jd_folder, jd_filename))

        # Run the main script to process the files using temporary folders
        process_files(temp_cv_folder, temp_jd_folder)

        # Redirect to the results page
        return redirect(url_for('results'))

    except Exception as e:
        app.logger.error(f"Error during file processing: {e}") # Log the error
        # Ensure temp_dir is cleaned up even if process_files fails
        error_message = f"An error occurred during processing: {str(e)}. Please check logs or try again."
        return render_template('results.html', error_message=error_message)
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@app.route('/results')
def results():
    # Define the path to the output CSV file using config
    output_csv_path = os.path.join(config.OUTPUT_DIR, config.OUTPUT_CSV_FILENAME)

    # Check if the output file exists
    if os.path.exists(output_csv_path):
        # Read the CSV file
        df = pd.read_csv(output_csv_path)

        # Convert the DataFrame to HTML
        csv_data = df.to_html(classes='table table-striped')

        # Render the HTML page with the CSV data
        return render_template('results.html', csv_data=csv_data)
    else:
        info_message = "No results available yet. This could be because no files were uploaded, or processing is not yet complete, or an error occurred."
        return render_template('results.html', info_message=info_message)


if __name__ == "__main__":
    app.run(debug=True)
