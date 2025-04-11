import os
import tempfile
import pdfplumber
import pandas as pd
from docx import Document
from typing import Dict, Any
from pathlib import Path
from utils.config import Config
import fitz  # PyMuPDF
from PIL import Image
import io

def handle_file_upload(uploaded_file) -> Dict[str, Any]:
    """Process uploaded file and return file info dictionary."""
    file_ext = Path(uploaded_file.name).suffix[1:].lower()
    
    if file_ext not in Config.SUPPORTED_FILE_TYPES:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Save file to temporary directory
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Extract content based on file type
    if file_ext == "pdf":
        content = extract_text_from_pdf(file_path)
    elif file_ext == "csv":
        content = extract_text_from_csv(file_path)
    elif file_ext == "docx":
        content = extract_text_from_docx(file_path)
    else:  # txt
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    
    return {
        "name": uploaded_file.name,
        "type": file_ext,
        "path": file_path,
        "size": round(uploaded_file.size / 1024, 2),  # KB
        "content": content
    }

def extract_text_from_file(file_info: Dict[str, Any]) -> str:
    """Extract text from file based on its type."""
    if file_info["type"] == "pdf":
        return extract_text_from_pdf(file_info["path"])
    elif file_info["type"] == "csv":
        return extract_text_from_csv(file_info["path"])
    elif file_info["type"] == "docx":
        return extract_text_from_docx(file_info["path"])
    else:  # txt
        with open(file_info["path"], "r", encoding="utf-8") as f:
            return f.read()

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    
    # Method 1: Use pdfplumber (good for text-based PDFs)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"pdfplumber failed: {str(e)}")
    
    # Method 2: Use PyMuPDF (good for scanned PDFs)
    if not text.strip():
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() or ""
        except Exception as e:
            print(f"PyMuPDF failed: {str(e)}")
    
    return text.strip()

def extract_text_from_csv(file_path: str) -> str:
    """Extract text from CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df.to_csv(index=False)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {str(e)}")

def get_file_preview(file_info: Dict[str, Any]) -> Any:
    """Get a preview of the file content based on its type."""
    if file_info["type"] == "csv":
        try:
            df = pd.read_csv(file_info["path"])
            return df.head(5)
        except Exception as e:
            return f"Error displaying CSV preview: {str(e)}"
    else:
        content = file_info["content"]
        return content[:1000] + "..." if len(content) > 1000 else content