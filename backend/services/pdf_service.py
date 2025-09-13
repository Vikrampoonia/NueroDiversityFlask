import os
import uuid
import fitz  # PyMuPDF
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

# --- Configuration ---
# All path definitions are removed from here. This service is now stateless.
# It will rely on the caller to provide paths.

# --- Service Functions ---

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a given PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Could not read PDF file at {pdf_path}: {e}")

def compress_pdf(input_pdf_path: str, output_dir: str) -> str:
    """
    Compresses a PDF and saves it to the specified output directory with a unique name.
    """
    try:
        doc = fitz.open(input_pdf_path)
        
        # THE FIX: Generate a unique filename to prevent race conditions.
        original_basename = os.path.basename(input_pdf_path).replace('.pdf', '')
        unique_filename = f"compressed_{original_basename}_{uuid.uuid4()}.pdf"
        unique_filepath = os.path.join(output_dir, unique_filename)

        # Save with garbage collection, deflation, and cleaning
        doc.save(unique_filepath, garbage=4, deflate=True, clean=True)
        doc.close()
        
        return unique_filepath
    except Exception as e:
        raise RuntimeError(f"Failed to compress PDF: {e}")


def create_dyslexia_friendly_pdf(html_content: str, output_dir: str, assets_dir: str) -> str:
    """
    Generates a dyslexia-friendly PDF and saves it to the specified output directory.
    """
    font_path_text = os.path.join(assets_dir, "fonts", "OpenDyslexic3-Regular.ttf")
    font_path_emoji = os.path.join(assets_dir, "fonts", "NotoColorEmoji-Regular.ttf")

    if not os.path.exists(font_path_text) or not os.path.exists(font_path_emoji):
        raise FileNotFoundError("Required font files are missing from the assets/fonts directory.")

    # Create HTML with embedded font face definitions, using the provided path
    html_with_fonts = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'OpenDyslexic';
                src: url('file://{font_path_text}') format('truetype');
            }}
            @font-face {{
                font-family: 'NotoEmoji';
                src: url('file://{font_path_emoji}') format('truetype');
            }}
            body {{
                font-family: 'OpenDyslexic', 'NotoEmoji', sans-serif;
                font-size: 18px; line-height: 1.8; word-spacing: 2px;
                letter-spacing: 1px; margin: 40px;
            }}
            p {{ margin-bottom: 15px; }}
            h1 {{ font-size: 28px; margin-bottom: 20px; }}
            h3 {{ font-size: 20px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # THE FIX: Generate a unique filename for the output PDF.
    unique_filename = f"dyslexic_friendly_{uuid.uuid4()}.pdf"
    unique_filepath = os.path.join(output_dir, unique_filename)

    font_config = FontConfiguration()
    HTML(string=html_with_fonts).write_pdf(unique_filepath, font_config=font_config)
    
    return unique_filepath

