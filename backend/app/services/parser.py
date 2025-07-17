import io
from typing import List, Dict, Any

# Import libraries for parsing
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import docx
except ImportError:
    docx = None
import email
from email import policy
from email.parser import BytesParser


def detect_file_type(filename: str) -> str:
    ext = filename.lower().split('.')[-1]
    if ext == 'pdf':
        return 'pdf'
    elif ext == 'docx':
        return 'docx'
    elif ext == 'eml':
        return 'eml'
    elif ext == 'txt':
        return 'txt'
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(' '.join(chunk))
        i += chunk_size - overlap
    return chunks


def parse_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    if not pdfplumber:
        raise ImportError("pdfplumber is not installed.")
    chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for idx, chunk in enumerate(chunk_text(text)):
                chunks.append({
                    "text": chunk,
                    "metadata": {"filename": filename, "page": page_num, "chunk_id": idx}
                })
    return chunks


def parse_docx(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    if not docx:
        raise ImportError("python-docx is not installed.")
    doc = docx.Document(io.BytesIO(file_bytes))
    full_text = '\n'.join([para.text for para in doc.paragraphs])
    return [
        {"text": chunk, "metadata": {"filename": filename, "page": 1, "chunk_id": idx}}
        for idx, chunk in enumerate(chunk_text(full_text))
    ]


def parse_txt(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    text = file_bytes.decode(errors='ignore')
    return [
        {"text": chunk, "metadata": {"filename": filename, "page": 1, "chunk_id": idx}}
        for idx, chunk in enumerate(chunk_text(text))
    ]


def parse_eml(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
    text = msg.get_body(preferencelist=('plain')).get_content() if msg.get_body(preferencelist=('plain')) else ''
    return [
        {"text": chunk, "metadata": {"filename": filename, "page": 1, "chunk_id": idx}}
        for idx, chunk in enumerate(chunk_text(text))
    ]


def parse_file(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    file_type = detect_file_type(filename)
    if file_type == 'pdf':
        return parse_pdf(file_bytes, filename)
    elif file_type == 'docx':
        return parse_docx(file_bytes, filename)
    elif file_type == 'txt':
        return parse_txt(file_bytes, filename)
    elif file_type == 'eml':
        return parse_eml(file_bytes, filename)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
