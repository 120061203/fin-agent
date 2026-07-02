import re
from typing import Any, Dict, List, Optional

import tiktoken

SECTION_PATTERNS = [
    re.compile(r"^\s*第[一二三四五六七八九十百千\d]+[章節條款項]\s*", re.MULTILINE),
    re.compile(r"^\s*\d+\.\s+[\w\u4e00-\u9fff]", re.MULTILINE),
    re.compile(r"^\s*[（(][一二三四五六七八九十\d]+[）)]\s*", re.MULTILINE),
]

MAX_TOKENS = 4000
OVERLAP_TOKENS = 200

_enc = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def _split_by_sections(text: str) -> List[Dict[str, str]]:
    combined = re.compile(
        "|".join(p.pattern for p in SECTION_PATTERNS), re.MULTILINE
    )
    matches = list(combined.finditer(text))
    if len(matches) < 2:
        return []

    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(
            {"title": match.group().strip(), "content": text[start:end].strip()}
        )
    return sections


def _sliding_window(
    text: str, pdf_id: str, start_n: int, section_title: Optional[str]
) -> List[Dict[str, Any]]:
    tokens = _enc.encode(text)
    chunks = []
    i = 0
    n = start_n
    while i < len(tokens):
        end = min(i + MAX_TOKENS, len(tokens))
        chunk_tokens = tokens[i:end]
        chunks.append(
            {
                "chunk_id": f"{pdf_id}_chunk_{n}",
                "content": _enc.decode(chunk_tokens),
                "section_title": section_title,
                "token_count": len(chunk_tokens),
                "page_start": 1,
                "page_end": 1,
            }
        )
        n += 1
        i += MAX_TOKENS - OVERLAP_TOKENS
    return chunks


def chunk_text(pages_text: List[str], pdf_id: str) -> List[Dict[str, Any]]:
    full_text = "\n".join(pages_text)
    sections = _split_by_sections(full_text)

    if sections:
        chunks: List[Dict[str, Any]] = []
        chunk_n = 0
        for section in sections:
            content = section["content"]
            tokens = _count_tokens(content)
            if tokens <= MAX_TOKENS:
                chunks.append(
                    {
                        "chunk_id": f"{pdf_id}_chunk_{chunk_n}",
                        "content": content,
                        "section_title": section["title"],
                        "token_count": tokens,
                        "page_start": 1,
                        "page_end": len(pages_text),
                    }
                )
                chunk_n += 1
            else:
                sub = _sliding_window(content, pdf_id, chunk_n, section["title"])
                chunks.extend(sub)
                chunk_n += len(sub)
        return chunks

    return _sliding_window(full_text, pdf_id, 0, None)
