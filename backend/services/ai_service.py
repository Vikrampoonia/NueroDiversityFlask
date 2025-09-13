import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils import parsers

# --- Initialization ---
load_dotenv()
# We now load the new GOOGLE_API_KEY from your .env file
api_key = os.getenv("GOOGLE_API_KEY")

try:
    # Configure the Google AI SDK with your API key
    genai.configure(api_key=api_key)
    
    # THE FIX: Using the best model for speed and capability.
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
    
    print("Google AI Service configured successfully.")
except Exception as e:
    print(f"Error configuring Google AI Service: {e}")
    model = None

# --- Helper function for chunking ---

def get_summary_in_chunks(text: str, chunk_size_words: int = 2000) -> str:
    """
    Handles very long texts by splitting them into chunks, summarizing each
    one, and then combining the summaries. This is still a best practice.
    """
    if not model:
        raise ConnectionError("Google AI Service is not configured properly.")

    words = text.split()
    if len(words) <= chunk_size_words:
        # If the text is short enough, summarize it in one go.
        # The prompt is now defined directly here.
        prompt = f"""
        Summarize the following text in a concise and meaningful way.
        Return only the summarized version without additional explanations.

        Text:
        {text}
        """
        response = model.generate_content(prompt)
        return response.text
    else:
        # If the text is too long, process it in chunks.
        summaries = []
        for i in range(0, len(words), chunk_size_words):
            chunk = " ".join(words[i:i + chunk_size_words])
            print(f"Summarizing chunk {i // chunk_size_words + 1}...")
            prompt = f"""
            Summarize the following text chunk in a concise and meaningful way.
            Return only the summarized version without additional explanations.

            Text:
            {chunk}
            """
            try:
                response = model.generate_content(prompt)
                summaries.append(response.text)
            except Exception as e:
                print(f"Error summarizing chunk: {e}")
                summaries.append(f"[Error processing chunk]")
        
        return "\n\n".join(s for s in summaries if s)

# --- Main Service Functions ---

def get_summary(text: str) -> str:
    """Calls the robust chunking helper to get a summary from Gemini."""
    return get_summary_in_chunks(text, chunk_size_words=2000)

def get_adhd_chapters(text: str) -> dict:
    """
    Generates ADHD-friendly chapters using a detailed prompt with Gemini.
    """
    if not model:
        raise ConnectionError("Google AI Service is not configured properly.")

    # The detailed prompt from your adhd.yaml file is now here.
    prompt = f"""
    Divide the following text into multiple parts or chapters to improve readability for ADHD users.
    Ensure logical segmentation, clear headings, and easy-to-understand language.

    Text:
    {text}

    For each chapter, include two multiple-choice questions. Each question should have four answer options, with one correct answer.

    Format the output EXACTLY as follows:

    Chapter 1: [Chapter Title]
    [Chapter Text]

    Q1: [Question 1]
    a) [Option 1] b) [Option 2] c) [Option 3] d) [Option 4]
    Correct Answer: [Correct option]

    Q2: [Question 2]
    a) [Option 1] b) [Option 2] c) [Option 3] d) [Option 4]
    Correct Answer: [Correct option]

    Chapter 2: [Chapter Title]
    [Chapter Text]

    Q1: [Question 1]
    a) [Option 1] b) [Option 2] c) [Option 3] d) [Option 4]
    Correct Answer: [Correct option]

    Q2: [Question 2]
    a) [Option 1] b) [Option 2] c) [Option 3] d) [Option 4]
    Correct Answer: [Correct option]

    [Repeat for all chapters]
    """

    response = model.generate_content(prompt)
    raw_text_result = response.text

    # We can still use our excellent parser to structure the output!
    structured_data = parsers.extract_chapters_and_questions(raw_text_result)
    return structured_data


