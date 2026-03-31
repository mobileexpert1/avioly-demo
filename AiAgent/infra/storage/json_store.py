from __future__ import annotations
import json
from pathlib import Path
from ...core.interfaces import DocumentStore
from ...core.types import RetrievedChunk

class JsonDocumentStore(DocumentStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def save_chunks(self, collection_id: str, chunks: list[RetrievedChunk]) -> None:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            data = []
        
        filtered = [item for item in data if item.get("collection_id") != collection_id]
        for chunk in chunks:
            filtered.append({
                "collection_id": collection_id,
                "document_name": chunk.document_name,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "metadata": chunk.metadata,
            })
        self.path.write_text(json.dumps(filtered, indent=2), encoding='utf-8')

    def list_documents(self, collection_id: str) -> list[str]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            docs = {item["document_name"] for item in data if item.get("collection_id") == collection_id}
            return sorted(list(docs))
        except Exception:
            return []
