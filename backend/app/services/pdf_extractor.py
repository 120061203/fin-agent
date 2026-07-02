from pathlib import Path
from typing import List, Tuple

import pdfplumber
import fitz  # pymupdf


def extract_text_from_pdf(file_path: str) -> Tuple[List[str], int, bool]:
    """
    Returns (pages_text, page_count, needs_ocr)
    """
    path = Path(file_path)
    pages_text: List[str] = []
    page_count = 0

    try:
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
    except Exception:
        try:
            doc = fitz.open(str(path))
            page_count = len(doc)
            pages_text = [page.get_text() for page in doc]
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Failed to extract PDF text: {e}")

    total_chars = sum(len(t) for t in pages_text)
    needs_ocr = page_count > 0 and total_chars < page_count * 50

    return pages_text, page_count, needs_ocr
