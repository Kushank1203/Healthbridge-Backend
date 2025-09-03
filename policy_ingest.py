import os, re, fitz
from typing import List

MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150

def read_pdf_text(pdf_path: str) -> str:
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def clean_text(t: str) -> str:
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()

def chunk_text(t: str, max_chars=MAX_CHUNK_CHARS, overlap=CHUNK_OVERLAP) -> List[str]:
    t = t.replace("\r\n", "\n")
    lines = t.split("\n")
    chunks, cur = [], ""
    for line in lines:
        if len(cur) + len(line) + 1 <= max_chars:
            cur += (line + "\n")
        else:
            chunks.append(cur.strip())
            cur = cur[-overlap:] + line + "\n"
    if cur.strip():
        chunks.append(cur.strip())
    # Minor filter to avoid tiny fragments
    return [c for c in chunks if len(c) > 200]
