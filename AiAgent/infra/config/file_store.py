from __future__ import annotations
import json
from pathlib import Path

from ...core.interfaces import ConfigStore
from ...core.types import CollectionContext

class JsonCollectionConfigStore(ConfigStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def get(self, collection_id: str) -> CollectionContext:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            for item in data:
                if item.get("collection_id") == collection_id:
                    return CollectionContext(
                        collection_id=item["collection_id"],
                        collection_name=item["collection_name"],
                        language=item.get("language", "en"),
                    )
        except Exception:
            pass
        return CollectionContext(collection_id=collection_id, collection_name=collection_id)

    def upsert(self, config: CollectionContext) -> None:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            data = []
        
        filtered = [item for item in data if item.get("collection_id") != config.collection_id]
        filtered.append({
            "collection_id": config.collection_id,
            "collection_name": config.collection_name,
            "language": config.language,
        })
        self.path.write_text(json.dumps(filtered, indent=2), encoding='utf-8')
