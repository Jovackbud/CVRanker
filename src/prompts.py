# --- System Prompts ---
# A system prompt defines the AI's persona and high-level instructions.
SUMMARIZER_SYSTEM_PROMPT = (
    "You are a hiring officer's personal assistant. You are experienced at the job and well known "
    "for your concise two paragraph summary style of about 50 words for each paragraph."
)

# --- User Prompts ---
# A user prompt provides the specific task and context.
SUMMARIZER_USER_PROMPT = (
    "The hiring officer wants you to help summarize the key skills and experiences of a CV an applicant "
    "submitted in two paragraphs of 100 words in total. He plans to read your summary and make a decision to hire or not hire each applicant "
    "respectively by comparing your summary of the applicant's skills and experiences with the Job description which "
    "he has and was already advertised. Make the first line a heading with only the applicant's name. Be careful to not "
    "miss any relevant experience or skill. This is the CV: {cv_text}"
)