import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.models.session import Session, SessionStatus
from app.models.pdf_doc import PDFDocument
from app.models.comparison import ComparisonJob


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._pdfs: Dict[str, PDFDocument] = {}
        self._jobs: Dict[str, ComparisonJob] = {}
        self._chroma_client = None

    def set_chroma_client(self, client):
        self._chroma_client = client

    def create_session(self) -> Session:
        session_id = str(uuid.uuid4())
        upload_dir = f"/tmp/sessions/{session_id}"
        os.makedirs(upload_dir, exist_ok=True)
        now = datetime.utcnow()
        session = Session(
            session_id=session_id,
            created_at=now,
            last_active_at=now,
            upload_dir=upload_dir,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def touch_session(self, session_id: str):
        session = self._sessions.get(session_id)
        if session:
            session.last_active_at = datetime.utcnow()

    def add_pdf(self, pdf: PDFDocument):
        self._pdfs[pdf.pdf_id] = pdf

    def get_pdf(self, pdf_id: str) -> Optional[PDFDocument]:
        return self._pdfs.get(pdf_id)

    def get_session_pdfs(self, session_id: str) -> List[PDFDocument]:
        return [p for p in self._pdfs.values() if p.session_id == session_id]

    def update_pdf_status(self, pdf_id: str, **kwargs):
        pdf = self._pdfs.get(pdf_id)
        if pdf:
            for k, v in kwargs.items():
                setattr(pdf, k, v)

    def delete_pdf(self, pdf_id: str):
        pdf = self._pdfs.pop(pdf_id, None)
        if pdf:
            if os.path.exists(pdf.file_path):
                os.remove(pdf.file_path)
            if self._chroma_client and pdf.chroma_collection:
                try:
                    self._chroma_client.delete_collection(pdf.chroma_collection)
                except Exception:
                    pass

    def add_job(self, job: ComparisonJob):
        self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Optional[ComparisonJob]:
        return self._jobs.get(job_id)

    def delete_session(self, session_id: str):
        pdfs = self.get_session_pdfs(session_id)
        for pdf in pdfs:
            self.delete_pdf(pdf.pdf_id)
        jobs = [j for j in self._jobs.values() if j.session_id == session_id]
        for job in jobs:
            self._jobs.pop(job.job_id, None)
        session = self._sessions.pop(session_id, None)
        if session and os.path.exists(session.upload_dir):
            shutil.rmtree(session.upload_dir, ignore_errors=True)
        if session:
            session.status = SessionStatus.cleaned

    def cleanup_expired(self) -> int:
        expired_ids = [
            sid for sid, s in self._sessions.items() if s.is_expired()
        ]
        for sid in expired_ids:
            self.delete_session(sid)
        return len(expired_ids)


session_manager = SessionManager()
