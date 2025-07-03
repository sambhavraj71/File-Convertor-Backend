# ==========================
# ✅ Updated backend/app.py with local storage support
# ==========================
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pdf2docx import Converter
from docx import Document
from PIL import Image
import os
import time
import PyPDF2
import tempfile

app = Flask(__name__)
CORS(app)

# Use system's temp directory for uploads
UPLOAD_FOLDER = tempfile.gettempdir()
# Use user's Downloads folder for output
OUTPUT_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def log(msg):
    print(f"[LOG] {msg}")

def unique_filename(extension):
    return f"converted_{int(time.time())}.{extension}"

@app.route('/convert/pdf-to-word', methods=['POST'])
def pdf_to_word():
    try:
        file = request.files['file']
        if not file:
            log("No file received")
            return jsonify({"status": "error", "message": "No file uploaded"})

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        log(f"File uploaded: {file_path}")

        output_name = unique_filename('docx')
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        log("Starting conversion PDF to Word")

        cv = Converter(file_path)
        cv.convert(output_path)
        cv.close()

        log("Conversion done")
        return jsonify({"status": "success", "filename": output_name})
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/convert/image-to-pdf', methods=['POST'])
def image_to_pdf():
    try:
        file = request.files['file']
        if not file:
            log("No image file received")
            return jsonify({"status": "error", "message": "No file uploaded"})
        log(f"Image uploaded: {file.filename}")

        img = Image.open(file.stream).convert('RGB')
        output_name = unique_filename('pdf')
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        log("Converting image to PDF")
        img.save(output_path)

        return jsonify({"status": "success", "filename": output_name})
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/convert/pdf-to-jpg', methods=['POST'])
def pdf_to_jpg():
    try:
        from pdf2image import convert_from_bytes
        file = request.files['file']
        if not file:
            log("No PDF received for JPG conversion")
            return jsonify({"status": "error", "message": "No file uploaded"})
        log(f"PDF uploaded for JPG conversion: {file.filename}")

        pages = convert_from_bytes(file.read())
        image_paths = []
        for i, page in enumerate(pages):
            name = f"page_{int(time.time())}_{i}.jpg"
            path = os.path.join(OUTPUT_FOLDER, name)
            page.save(path, 'JPEG')
            image_paths.append(name)
        log(f"Saved {len(image_paths)} JPG files")
        return jsonify({"status": "success", "filenames": image_paths})
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/convert/merge-pdf', methods=['POST'])
def merge_pdf():
    try:
        files = request.files.getlist("files")
        if not files:
            log("No PDFs received to merge")
            return jsonify({"status": "error", "message": "No files uploaded"})

        merger = PyPDF2.PdfMerger()
        for file in files:
            log(f"Adding file to merge: {file.filename}")
            merger.append(file)

        output_name = unique_filename("pdf")
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        merger.write(output_path)
        merger.close()

        log("Merged PDF created")
        return jsonify({"status": "success", "filename": output_name})
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/convert/extract-pdf', methods=['POST'])
def extract_pdf():
    try:
        file = request.files['file']
        start = int(request.form['start'])
        end = int(request.form['end'])

        if not file:
            log("No file uploaded for extraction")
            return jsonify({"status": "error", "message": "No file uploaded"})
        log(f"PDF uploaded for extraction: {file.filename}, pages {start}-{end}")

        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()

        for page in range(start - 1, end):
            pdf_writer.add_page(pdf_reader.pages[page])

        output_name = unique_filename("pdf")
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        with open(output_path, 'wb') as f:
            pdf_writer.write(f)

        log("Extracted pages PDF created")
        return jsonify({"status": "success", "filename": output_name})
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    log(f"Download request for: {filename}")
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    log("Starting backend Flask server on http://localhost:5000")
    log(f"Uploads will be stored in: {UPLOAD_FOLDER}")
    log(f"Converted files will be saved to: {OUTPUT_FOLDER}")
    app.run(debug=True)