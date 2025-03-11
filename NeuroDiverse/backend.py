import os
import json
import tempfile
from flask import Flask, request, jsonify, send_file, send_from_directory
import fitz  # PyMuPDF
from gtts import gTTS
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from gptRun import gptResponse, getSummary, gptQuestion, gptQuestion1
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
TEXT_JSON_FILE = os.path.join(BASE_DIR, "text.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "chapters.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font paths
FONT_PATH_TEXT = os.path.join(BASE_DIR, "OpenDyslexic3-Regular.ttf")
FONT_PATH_EMOJI = os.path.join(BASE_DIR, "NotoColorEmoji-Regular.ttf")

# Check font existence
for font in [FONT_PATH_TEXT, FONT_PATH_EMOJI]:
    if not os.path.exists(font):
        print(f"Warning: Font '{font}' not found. PDF styling may be affected.")

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text")
    return text

# Save text to JSON
def save_text_to_json(extracted_text):
    with open(TEXT_JSON_FILE, "w", encoding="utf-8") as json_file:
        json.dump({"text": extracted_text}, json_file, indent=4, ensure_ascii=False)

# Read text from JSON
def read_text_from_json():
    if not os.path.exists(TEXT_JSON_FILE):
        return {"error": "text.json file not found."}
    try:
        with open(TEXT_JSON_FILE, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        return {"text": data.get("text", "")}
    except json.JSONDecodeError:
        return {"error": "text.json is corrupted or empty."}

# Generate Dyslexic-friendly PDF
def create_pdf_with_html(text, output_filename):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <style>
            @font-face {{ font-family: 'OpenDyslexic'; src: url('file://{os.path.abspath(FONT_PATH_TEXT)}') format('truetype'); }}
            @font-face {{ font-family: 'NotoEmoji'; src: url('file://{os.path.abspath(FONT_PATH_EMOJI)}') format('truetype'); }}
            body {{ font-family: 'OpenDyslexic', 'NotoEmoji', sans-serif; font-size: 30px; line-height: 2; }}
        </style>
    </head>
    <body>
        {text.replace('\n', '<br>')}
    </body>
    </html>
    """
    HTML(string=html_content).write_pdf(output_filename, font_config=FontConfiguration())
    return output_filename

# Upload PDF and Extract Text API
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    extracted_text = extract_text_from_pdf(file_path)
    save_text_to_json(extracted_text)
    
    return jsonify({
        'message': 'Text extracted successfully', 
        'filePath': file_path,
        'fileName': file.filename
    })

# Serve static files
@app.route('/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    # This route will serve files from OUTPUT_DIR
    return send_from_directory(OUTPUT_DIR, filename)

# Text-to-Speech API - Match the frontend endpoint
@app.route('/text_to_speech', methods=['GET'])
def text_to_speech():
    file_name = request.args.get("file_name")

    if not file_name:
        return jsonify({"error": "Missing file_name parameter"}), 400

    text_data = read_text_from_json()  # Fetch extracted text

    # Ensure text_data contains valid text
    if isinstance(text_data, dict) and "text" in text_data:
        extracted_text = text_data["text"].strip()
    else:
        return jsonify({"error": "Failed to retrieve valid text"}), 400

    if not extracted_text:
        return jsonify({"error": "No valid text found for TTS conversion"}), 400

    audio_file_path = os.path.join(OUTPUT_DIR, "output.mp3")

    try:
        # Convert text to speech
        tts = gTTS(text=extracted_text, lang="hi")
        tts.save(audio_file_path)

        return send_file(audio_file_path, mimetype="audio/mpeg", as_attachment=False)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Generate Dyslexic-friendly PDF API - Match the frontend endpoint
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    text_data = read_text_from_json()
    if "error" in text_data:
        return jsonify(text_data), 400
    
    try:
        processed_text = gptResponse(text_data["text"])
    except Exception as e:
        processed_text = text_data["text"]
        print(f"Error in gptResponse: {str(e)}")
    
    output_pdf = os.path.join(OUTPUT_DIR, "dyslexic_friendly.pdf")
    try:
        create_pdf_with_html(processed_text, output_pdf)
        
        # Send the PDF file to the frontend
        return send_file(output_pdf, as_attachment=True, download_name="dyslexic_friendly.pdf", mimetype="application/pdf")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Summarize API - Match the frontend endpoint
@app.route('/summarize', methods=['POST'])
def summarize():
    text_data = read_text_from_json()
    if "error" in text_data:
        return jsonify(text_data), 400
    
    summary = getSummary(text_data["text"])
    
    return jsonify({
        "message": "Summary generated successfully.",
        "summary": summary
    })



# Function to save data to JSON
def save_to_json(data):
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):  # Ensure it's a list
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    if isinstance(data, list):  # Ensure proper appending
        existing_data.extend(data)
    else:
        existing_data.append(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)


def load_text():
    try:
        with open("text.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("text", "")  # Get the text key, default to empty string if missing
    except Exception as e:
        return str(e)

# Function to call GPT (Mocked function for now)


# Function to save processed data


@app.route("/generate-story", methods=["POST"])
def generate_story():
    try:
        input_text = load_text()  # Load text from text.json

        if not input_text:
            return jsonify({"error": "No text found in text.json"}), 400

        result = gptQuestion(input_text)  # Generate story

        if not isinstance(result, list):  # Ensure valid response format
            return jsonify({"error": "Invalid response format from gptQuestion"}), 500

        save_to_json(result)  # Save processed story

        return jsonify({"message": "Story generated successfully", "story": result}), 200

    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/process1", methods=["POST"])
def process_data_1():
    try:
        result = gptQuestion1()  

        if not isinstance(result, (list, str)):  # Accept list or string
            return jsonify({"error": "Invalid response format from gptQuestion1"}), 500
        
        # Save as JSON (ensure consistent format)
        save_to_json(result if isinstance(result, list) else [result])  

        return jsonify({"message": "Data saved successfully", "data": result}), 200

    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def load_story_data():
    with open("chapters.json", "r", encoding="utf-8") as file:
        return json.load(file)

@app.route("/get-story", methods=["GET"])
def get_story():
    try:
        story_data = load_story_data()
        return jsonify(story_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)