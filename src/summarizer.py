import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the generative AI model
api_key = os.getenv('google_ai_studio_key')
genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="You are a hiring officer's personal assistant. You are experienced at the job and well known "
                       "for your concise two paragraph summary style of about 50 words for each paragraph."
)


def summarize_cv(cv_text):
    """
    Summarizes the skills and experiences in a CV using a generative model.
    """
    prompt = f""" The hiring officer wants you to help summarize the key skills and experiences of a CV an applicant 
    submitted in two paragraphs. He plans to read your summary and make a decision to hire or not hire each applicant 
    respectively by comparing your summary of the applicant's skills and experiences with the Job description which 
    he has and was already advertised. Make the first line a heading with only applicants name. Be careful to not 
    miss any relevant experience or skill. This is the CV: {cv_text}
    """
    response = model.generate_content(prompt)
    return response.text
