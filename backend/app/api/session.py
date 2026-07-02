from fastapi import APIRouter, HTTPException
from app.services.session_manager import session_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", status_code=201)
async def create_session():
    session = session_manager.create_session()
    return {
        "session_id": session.session_id,
        "expires_at": session.expires_at.isoformat() + "Z",
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    pdfs = session_manager.get_session_pdfs(session_id)
    return {
        "session_id": session.session_id,
        "status": session.status,
        "pdf_count": len(pdfs),
        "expires_at": session.expires_at.isoformat() + "Z",
    }


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session_manager.delete_session(session_id)


@router.post("/{session_id}/cleanup", status_code=204)
async def cleanup_session(session_id: str):
    """Beacon-compatible cleanup endpoint (POST for sendBeacon)."""
    session = session_manager.get_session(session_id)
    if session:
        session_manager.delete_session(session_id)
