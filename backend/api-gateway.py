import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
import logging

from celery_worker import celery_app, compress_pdf_task, generate_audio_task, generate_dyslexic_pdf_task
from services import pdf_service, ai_service

# --- App Initialization and Configuration ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Use absolute paths based on the file's location for robustness
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploaded_files')
app.config['PROCESSED_FILES_DIR'] = os.path.join(BASE_DIR, 'processed_files')
app.config['ASSETS_DIR'] = os.path.join(BASE_DIR, 'assets')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FILES_DIR'], exist_ok=True)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# --- Helper Function for File Handling ---
def save_uploaded_file():
    if 'file' not in request.files:
        return None, "No file part in the request."
    file = request.files['file']
    if file.filename == '':
        return None, "No file selected."
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath, None
    return None, "An unknown error occurred while saving the file."

# --- API ROUTES ---

@app.route('/api/process-text-from-pdf', methods=['POST'])
def process_text_from_pdf():
    filepath, error = save_uploaded_file()
    if error:
        return jsonify({"error": error}), 400
    try:
        text = pdf_service.extract_text_from_pdf(filepath)
        if not text:
            return jsonify({"error": "Could not extract text from PDF."}), 400
        return jsonify({"result": text}), 200
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

@app.route('/api/process-text', methods=['POST'])
def process_text():
    data = request.get_json()
    if not data or 'operation' not in data or 'text' not in data:
        return jsonify({"error": "Missing 'operation' or 'text' in request body"}), 400
    try:
        if data['operation'] == 'summarize':
            result = ai_service.get_summary(data['text'])
        elif data['operation'] == 'adhd_chapters':
            result = ai_service.get_adhd_chapters(data['text'])
        else:
            return jsonify({"error": f"Unknown operation: {data['operation']}"}), 400
        return jsonify({"result": result}), 200
    except Exception as e:
        app.logger.error(f"An error occurred in /api/process-text: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/pdf-to-speech', methods=['POST'])
def pdf_to_speech_endpoint():
    filepath, error = save_uploaded_file()
    if error:
        return jsonify({"error": error}), 400
    text = pdf_service.extract_text_from_pdf(filepath)
    os.remove(filepath)
    if not text:
        return jsonify({"error": "Could not extract text from PDF."}), 400
    task = generate_audio_task.delay(text, app.config['PROCESSED_FILES_DIR'])
    return jsonify({"task_id": task.id}), 202

@app.route('/api/generate-dyslexic-pdf', methods=['POST'])
def dyslexic_pdf_endpoint():
    filepath, error = save_uploaded_file()
    if error:
        return jsonify({"error": error}), 400
    text = pdf_service.extract_text_from_pdf(filepath)
    os.remove(filepath)
    if not text:
        return jsonify({"error": "Could not extract text from PDF."}), 400
    task = generate_dyslexic_pdf_task.delay(
        text, 
        app.config['PROCESSED_FILES_DIR'], 
        app.config['ASSETS_DIR']
    )
    return jsonify({"task_id": task.id}), 202

@app.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task_result = AsyncResult(task_id, app=celery_app)
    
    # THE FIX: This is the critical change for local testing.
    # When tasks run eagerly, their state is always SUCCESS or FAILURE immediately.
    # We check if the backend is disabled, and if so, we know the task is already complete.
    if celery_app.conf.task_always_eager and task_result.backend.__class__.__name__ == 'DisabledBackend':
        # In this mode, the task has already run. We can directly access the result.
        response = {
            "task_id": task_id,
            "state": task_result.state, # Will be SUCCESS or FAILURE
            "result": os.path.basename(task_result.result) if task_result.successful() and task_result.result else str(task_result.info),
        }
    else:
        # This is the normal flow for when Redis is connected.
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "result": os.path.basename(task_result.result) if task_result.successful() and task_result.result else str(task_result.info),
        }
    return jsonify(response), 200

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FILES_DIR'], filename, as_attachment=True)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

