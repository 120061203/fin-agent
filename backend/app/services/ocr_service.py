import io
from typing import List

import fitz  # pymupdf
import pytesseract
from PIL import Image


def ocr_pdf(file_path: str) -> List[str]:
    """OCR fallback for scanned PDFs."""
    doc = fitz.open(file_path)
    pages_text: List[str] = []

    for page in doc:
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img, lang="chi_tra+eng")
        pages_text.append(text)

    doc.close()
    return pages_text
