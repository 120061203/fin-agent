from typing import Any, Dict, List, Optional

import chromadb

_client: Optional[chromadb.EphemeralClient] = None


def set_client(client: chromadb.EphemeralClient):
    global _client
    _client = client


def _get_client() -> chromadb.EphemeralClient:
    global _client
    if _client is None:
        _client = chromadb.EphemeralClient()
    return _client


def index_chunks(pdf_id: str, chunks: List[Dict[str, Any]]) -> str:
    client = _get_client()
    collection_name = f"doc_{pdf_id.replace('-', '_')}"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    if not chunks:
        return collection_name

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["content"] for c in chunks],
        metadatas=[
            {
                "section_title": c.get("section_title") or "",
                "token_count": c["token_count"],
                "page_start": c.get("page_start", 1),
                "page_end": c.get("page_end", 1),
            }
            for c in chunks
        ],
    )
    return collection_name


def search(pdf_id: str, query: str, top_k: int = 3) -> List[str]:
    client = _get_client()
    collection_name = f"doc_{pdf_id.replace('-', '_')}"
    try:
        collection = client.get_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


def delete_collection(pdf_id: str):
    client = _get_client()
    collection_name = f"doc_{pdf_id.replace('-', '_')}"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
