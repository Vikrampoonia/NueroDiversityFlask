import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv

# --- Initialization ---
# This service will use the same API key and configuration as our ai_service
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# It's good practice to ensure the service is configured on startup.
if api_key:
    genai.configure(api_key=api_key)
    # For TTS, we can use a specific model optimized for speech synthesis.
    tts_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-tts')
else:
    print("Warning: GOOGLE_API_KEY not found. Audio service will not work.")
    tts_model = None

# --- Service Function ---

def convert_text_to_speech(text: str, output_dir: str, lang: str = 'en-US') -> str:
    """
    Converts a string of text to an MP3 file using the Google AI TTS API
    and saves it to a specified directory with a unique name.

    Args:
        text (str): The text to convert.
        output_dir (str): The directory where the generated file will be saved.
        lang (str): The language code (e.g., 'en-US', 'es-ES', 'hi-IN').

    Returns:
        str: The full file path of the generated MP3 audio file.
    """
    if not text.strip():
        raise ValueError("Cannot convert empty text to speech.")
    
    if not tts_model:
        raise ConnectionError("Google AI (TTS) Service is not configured properly.")

    try:
        # Generate the audio content directly from the API
        response = genai.text_to_speech(
            text=text,
            model=tts_model,
            voice_config={"language_code": lang}
        )
        
        # THE FIX: Generate a unique filename to prevent race conditions.
        unique_filename = f"speech_{uuid.uuid4()}.mp3"
        unique_filepath = os.path.join(output_dir, unique_filename)

        # The API returns the raw audio data (bytes). We write these bytes to a file.
        with open(unique_filepath, "wb") as f:
            f.write(response.audio_content)
            
        return unique_filepath

    except Exception as e:
        # Catch potential API errors
        raise RuntimeError(f"Failed to generate speech via Google AI API: {e}")

