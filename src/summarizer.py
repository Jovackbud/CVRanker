import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from src import config

# Load environment variables from .env file
load_dotenv()

# Configure the generative AI model
api_key = os.getenv('google_ai_studio_key')
if not api_key:
    raise ValueError("API key for Gemini not found or empty. Please set the google_ai_studio_key environment variable.")
try:
    genai.configure(api_key=api_key)
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API for summarizer: {e}")

try:
    generator_model = genai.GenerativeModel(
        model_name=config.SUMMARY_GENERATION_MODEL,
        system_instruction="You are a hiring officer's personal assistant. You are experienced at the job and well known "
                           "for your concise two paragraph summary style of about 50 words for each paragraph."
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize GenerativeModel for summarizer: {e}")

def summarize_cv(cv_text, filename="Unknown Applicant"):
    """
    Summarizes the skills and experiences in a CV using a generative model,
    and extracts the applicant's name. Returns a JSON-like dictionary.
    """
    prompt = f"""
    The hiring officer wants you to help summarize the key skills and experiences of a CV an applicant
    submitted. He plans to read your summary and make a decision to hire or not hire each applicant
    respectively by comparing your summary of the applicant's skills and experiences with the Job description which
    he has and was already advertised.

    Please provide the output as a JSON object with two keys:
    1.  "applicant_name": Extract the applicant's full name from the CV. If the name is not explicitly found, use the CV filename '{filename}'.
    2.  "summary": A concise two-paragraph summary of about 50 words for each paragraph (100 words total) focusing on key skills and experiences relevant to a job application.

    This is the CV text:
    {cv_text}
    """
    try:
        response = generator_model.generate_content(prompt)
        # Attempt to find JSON within the response text if the model adds extra text
        raw_text = response.text
        json_start = raw_text.find('{')
        json_end = raw_text.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = raw_text[json_start:json_end]
            parsed_json = json.loads(json_str)
            # Ensure both keys are present, providing defaults if not
            if 'applicant_name' not in parsed_json:
                parsed_json['applicant_name'] = filename
            if 'summary' not in parsed_json:
                parsed_json['summary'] = "Summary could not be extracted."
            return parsed_json
        else:
            # Fallback if no JSON object is found
            return {'applicant_name': filename, 'summary': 'Error extracting summary - No valid JSON found in model output.'}

    except json.JSONDecodeError:
        return {'applicant_name': filename, 'summary': 'Error extracting summary - model output was not valid JSON.'}
    except Exception as e:
        # General exception for other issues (e.g., API errors)
        error_message = f"Gemini summarization failed for CV '{filename}': {str(e)}"
        # Log the error message or handle it as needed
        print(error_message) # Basic logging
        return {'applicant_name': filename, 'summary': f"Error during summarization: {str(e)}"}