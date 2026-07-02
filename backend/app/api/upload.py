import asyncio
import os
import uuid
from datetime import datetime

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.pdf_doc import PDFDocument, PDFStatus
from app.services.session_manager import session_manager
from app.services import pdf_extractor, ocr_service, chunker, indexer

router = APIRouter(prefix="/api/sessions", tags=["pdfs"])

MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_PDFS_PER_SESSION = 10


async def _process_pdf(pdf_id: str, file_path: str):
    try:
        session_manager.update_pdf_status(pdf_id, status=PDFStatus.processing)
        pages_text, page_count, needs_ocr = pdf_extractor.extract_text_from_pdf(file_path)
        if needs_ocr:
            pages_text = await asyncio.get_event_loop().run_in_executor(
                None, ocr_service.ocr_pdf, file_path
            )
        chunks = chunker.chunk_text(pages_text, pdf_id)
        collection_name = indexer.index_chunks(pdf_id, chunks)
        session_manager.update_pdf_status(
            pdf_id,
            status=PDFStatus.ready,
            page_count=page_count,
            ocr_used=needs_ocr,
            chunk_count=len(chunks),
            chroma_collection=collection_name,
        )
    except Exception as e:
        session_manager.update_pdf_status(
            pdf_id, status=PDFStatus.error, error_message=str(e)
        )


@router.post("/{session_id}/pdfs", status_code=202)
async def upload_pdf(session_id: str, file: UploadFile = File(...)):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    existing = session_manager.get_session_pdfs(session_id)
    if len(existing) >= MAX_PDFS_PER_SESSION:
        raise HTTPException(status_code=409, detail=f"Session PDF limit ({MAX_PDFS_PER_SESSION}) reached")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 100MB limit")

    pdf_id = str(uuid.uuid4())
    file_path = os.path.join(session.upload_dir, f"{pdf_id}.pdf")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    pdf = PDFDocument(
        pdf_id=pdf_id,
        session_id=session_id,
        filename=file.filename,
        file_path=file_path,
        file_size_bytes=len(content),
        uploaded_at=datetime.utcnow(),
    )
    session_manager.add_pdf(pdf)
    session_manager.touch_session(session_id)
    asyncio.create_task(_process_pdf(pdf_id, file_path))

    return {
        "pdf_id": pdf_id,
        "filename": file.filename,
        "file_size_bytes": len(content),
        "status": "processing",
    }


@router.get("/{session_id}/pdfs")
async def list_pdfs(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    pdfs = session_manager.get_session_pdfs(session_id)
    session_manager.touch_session(session_id)
    return {
        "pdfs": [
            {
                "pdf_id": p.pdf_id,
                "filename": p.filename,
                "file_size_bytes": p.file_size_bytes,
                "page_count": p.page_count,
                "status": p.status,
                "ocr_used": p.ocr_used,
                "chunk_count": p.chunk_count,
                "uploaded_at": p.uploaded_at.isoformat() + "Z",
                "error_message": p.error_message,
            }
            for p in pdfs
        ]
    }


@router.delete("/{session_id}/pdfs/{pdf_id}", status_code=204)
async def delete_pdf(session_id: str, pdf_id: str):
    pdf = session_manager.get_pdf(pdf_id)
    if not pdf or pdf.session_id != session_id:
        raise HTTPException(status_code=404, detail="PDF not found")
    session_manager.delete_pdf(pdf_id)
