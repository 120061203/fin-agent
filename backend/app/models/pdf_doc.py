from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PDFStatus(str, Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    error = "error"


@dataclass
class PDFDocument:
    pdf_id: str
    session_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    uploaded_at: datetime
    status: PDFStatus = PDFStatus.uploading
    ocr_used: Optional[bool] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    chroma_collection: Optional[str] = None
    error_message: Optional[str] = None
