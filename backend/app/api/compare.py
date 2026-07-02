import asyncio
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.comparison import ComparisonJob, ComparisonStatus
from app.models.pdf_doc import PDFStatus
from app.services import agent
from app.services.session_manager import session_manager

router = APIRouter(prefix="/api/sessions", tags=["compare"])


class CompareRequest(BaseModel):
    pdf_id_a: str
    pdf_id_b: str


@router.post("/{session_id}/compare", status_code=202)
async def start_comparison(session_id: str, req: CompareRequest):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if req.pdf_id_a == req.pdf_id_b:
        raise HTTPException(status_code=400, detail="pdf_id_a and pdf_id_b must be different")

    pdf_a = session_manager.get_pdf(req.pdf_id_a)
    pdf_b = session_manager.get_pdf(req.pdf_id_b)

    if not pdf_a or pdf_a.session_id != session_id:
        raise HTTPException(status_code=404, detail=f"PDF {req.pdf_id_a} not found")
    if not pdf_b or pdf_b.session_id != session_id:
        raise HTTPException(status_code=404, detail=f"PDF {req.pdf_id_b} not found")
    if pdf_a.status != PDFStatus.ready:
        raise HTTPException(status_code=409, detail=f"PDF {req.pdf_id_a} is not ready (status: {pdf_a.status})")
    if pdf_b.status != PDFStatus.ready:
        raise HTTPException(status_code=409, detail=f"PDF {req.pdf_id_b} is not ready (status: {pdf_b.status})")

    job_id = str(uuid.uuid4())
    job = ComparisonJob(
        job_id=job_id,
        session_id=session_id,
        pdf_id_a=req.pdf_id_a,
        pdf_id_b=req.pdf_id_b,
        created_at=datetime.utcnow(),
        status=ComparisonStatus.queued,
    )
    session_manager.add_job(job)

    return {
        "job_id": job_id,
        "status": "running",
        "stream_url": f"/api/sessions/{session_id}/compare/{job_id}/stream",
    }


@router.get("/{session_id}/compare/{job_id}/stream")
async def stream_comparison(session_id: str, job_id: str):
    job = session_manager.get_job(job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        try:
            async for step in agent.run_comparison(job):
                data = json.dumps(
                    {"step": step.step_id, "type": step.type, "content": step.content},
                    ensure_ascii=False,
                )
                yield f"event: reasoning_step\ndata: {data}\n\n"

            if job.report_markdown:
                report_data = json.dumps({"markdown": job.report_markdown}, ensure_ascii=False)
                yield f"event: report\ndata: {report_data}\n\n"

            if job.status == ComparisonStatus.error:
                error_data = json.dumps({"message": job.error_message or "Unknown error"}, ensure_ascii=False)
                yield f"event: error\ndata: {error_data}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/{session_id}/compare/{job_id}")
async def get_job(session_id: str, job_id: str):
    job = session_manager.get_job(job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "pdf_id_a": job.pdf_id_a,
        "pdf_id_b": job.pdf_id_b,
        "report_markdown": job.report_markdown,
        "completed_at": job.completed_at.isoformat() + "Z" if job.completed_at else None,
    }
