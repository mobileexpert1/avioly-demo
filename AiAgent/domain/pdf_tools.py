from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader
import re

from ..core.types import RetrievedChunk

@dataclass(frozen=True)
class PdfPageChunk:
    page_number: int
    text: str
    raw_text: str
    metadata: dict[str, object]

def extract_pdf_pages(pdf_path: Path) -> list[PdfPageChunk]:
    reader = PdfReader(str(pdf_path))
    pages: list[PdfPageChunk] = []
    for index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned = normalize_text(raw_text)
        if not cleaned: continue
        pages.append(
            PdfPageChunk(
                page_number=index,
                text=cleaned,
                raw_text=raw_text,
                metadata={"page_number": index}
            )
        )
    return pages

def normalize_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\bwww\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_chunks(collection_id: str, pdf_path: Path) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    for page in extract_pdf_pages(pdf_path):
        page_chunks = split_page_into_chunks(page.raw_text, chunk_size=300, overlap=50)
        for chunk_index, text in enumerate(page_chunks):
            chunks.append(
                RetrievedChunk(
                    source_id=collection_id,
                    document_name=pdf_path.name,
                    chunk_index=chunk_index,
                    text=text,
                    metadata={
                        **page.metadata,
                        "chunk_index": chunk_index,
                    },
                )
            )
    return chunks

def split_page_into_chunks(page_text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    if not page_text: return []
    page_text = normalize_text(page_text)
    words = page_text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += (chunk_size - overlap)
        
    return chunks
