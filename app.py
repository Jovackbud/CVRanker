from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
from main import main as process_files

# Set the folders to store the uploaded files
CV_FOLDER = 'dataset/cvs'
JD_FOLDER = 'dataset/jd'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['CV_FOLDER'] = CV_FOLDER
app.config['JD_FOLDER'] = JD_FOLDER

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
        return 'No file part', 400

    cv_files = request.files.getlist('cv_files')
    jd_file = request.files['jd_file']

    # Save CV files
    for file in cv_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['CV_FOLDER'], filename))

    # Save JD file
    if jd_file and allowed_file(jd_file.filename):
        jd_filename = secure_filename(jd_file.filename)
        jd_file.save(os.path.join(app.config['JD_FOLDER'], jd_filename))

    # Run the main script to process the files
    process_files()

    # Redirect to the results page
    return redirect(url_for('results'))

@app.route('/results')
def results():
    # Serve the output CSV
    output_path = 'output.csv'
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            csv_data = f.read()
        return render_template('results.html', csv_data=csv_data)  # Create a results.html page
    else:
        return "No results available yet.", 400

if __name__ == "__main__":
    app.run(debug=True)
