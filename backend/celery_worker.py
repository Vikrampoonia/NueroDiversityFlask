import os
from celery import Celery

# Import our refactored service modules
from services import audio_service, pdf_service, ai_service
from utils import parsers

# --- LOCAL TESTING CONFIGURATION ---
celery_app = Celery('tasks')

# THE FIX: We are enabling a result backend specifically for local testing.
# 'rpc://' creates a transient, in-memory backend that allows us to get
# task results without needing Redis.
celery_app.conf.update(
    task_always_eager=True,  # Bypasses the message broker.
    result_backend='rpc://'  # Enables storing results for status checks.
)


# --- Task Definitions ---
# (The rest of the file remains exactly the same)

@celery_app.task(name='tasks.generate_audio')
def generate_audio_task(text: str, output_dir: str, lang: str = 'en-US') -> str:
    """Asynchronous task to generate an audio file."""
    try:
        file_path = audio_service.convert_text_to_speech(text, output_dir, lang)
        return file_path
    except Exception as e:
        print(f"Error in generate_audio_task: {e}")
        raise e

@celery_app.task(name='tasks.compress_pdf')
def compress_pdf_task(input_pdf_path: str, output_dir: str) -> str:
    """Asynchronous task to compress a PDF."""
    try:
        compressed_path = pdf_service.compress_pdf(input_pdf_path, output_dir)
        # Clean up the original uploaded file
        if os.path.exists(input_pdf_path):
            os.remove(input_pdf_path)
        return compressed_path
    except Exception as e:
        if os.path.exists(input_pdf_path):
            os.remove(input_pdf_path)
        print(f"Error in compress_pdf_task: {e}")
        raise e

@celery_app.task(name='tasks.generate_dyslexic_pdf')
def generate_dyslexic_pdf_task(text: str, output_dir: str, assets_dir: str) -> str:
    """Asynchronous task to create a dyslexia-friendly PDF."""
    try:
        # Step 1: Get structured data from the AI service
        structured_data = ai_service.get_adhd_chapters(text)
        # Step 2: Format that data into HTML using our parser utility
        html_content = parsers.format_chapters_to_html(structured_data)
        # Step 3: Generate the PDF from the HTML, using the provided paths
        pdf_path = pdf_service.create_dyslexia_friendly_pdf(html_content, output_dir, assets_dir)
        return pdf_path
    except Exception as e:
        print(f"Error in generate_dyslexic_pdf_task: {e}")
        raise e

