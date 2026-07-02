import asyncio
import os
from contextlib import asynccontextmanager

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import session, upload, compare
from app.services.session_manager import session_manager
from app.services import indexer

load_dotenv()


async def _ttl_cleanup_task():
    while True:
        await asyncio.sleep(60)
        cleaned = session_manager.cleanup_expired()
        if cleaned:
            print(f"[TTL] Cleaned {cleaned} expired session(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    litellm_url = os.getenv("LITELLM_BASE_URL")
    if not litellm_url:
        print("WARNING: LITELLM_BASE_URL not set")
    os.makedirs("/tmp/sessions", exist_ok=True)

    chroma_client = chromadb.EphemeralClient()
    session_manager.set_chroma_client(chroma_client)
    indexer.set_client(chroma_client)
    app.state.chroma_client = chroma_client

    task = asyncio.create_task(_ttl_cleanup_task())
    yield
    task.cancel()


app = FastAPI(title="PDF Compare Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(upload.router)
app.include_router(compare.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
