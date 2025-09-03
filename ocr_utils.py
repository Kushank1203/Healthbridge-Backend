import pytesseract
from PIL import Image
import io
import fitz  # PyMuPDF
import tempfile
import docx2txt
import os


def extract_text_from_file(file_bytes, filename: str):
    ext = filename.lower().split(".")[-1]
    
    if ext in ["jpg", "jpeg", "png"]:
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)
    
    elif ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    
    elif ext == "docx":
        return extract_text_from_docx(file_bytes)
    
    else:
        return "Unsupported file format."

def extract_text_from_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        text = docx2txt.process(tmp.name)
    os.remove(tmp.name)
    return text
