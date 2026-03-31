from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..core.interfaces import ConversationRepository
from ..core.models import ConversationPage, ConversationPageResult, ConversationThread


class SQLiteConversationRepository(ConversationRepository):
    def __init__(self, database_path: str) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def load_threads(self, page: ConversationPage) -> ConversationPageResult:
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, title, updated_at, preview
                FROM conversation_threads
                ORDER BY updated_at DESC
                LIMIT ?
                OFFSET ?
                """,
                (page.limit, self._offset_from_cursor(page.cursor)),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM conversation_threads").fetchone()[0]

        items = [
            ConversationThread(
                id=row["id"],
                title=row["title"],
                updated_at=row["updated_at"],
                preview=row["preview"],
            )
            for row in rows
        ]
        next_offset = self._offset_from_cursor(page.cursor) + len(items)
        has_more = next_offset < total
        return ConversationPageResult(
            items=items,
            next_cursor=str(next_offset) if has_more else None,
            has_more=has_more,
        )

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_threads (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    preview TEXT
                )
                """
            )
            conn.commit()

    def _offset_from_cursor(self, cursor: str | None) -> int:
        if not cursor:
            return 0
        return int(cursor)


class JsonConversationRepository(ConversationRepository):
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)

    def load_threads(self, page: ConversationPage) -> ConversationPageResult:
        data = json.loads(self._path.read_text()) if self._path.exists() else []
        offset = int(page.cursor or 0)
        chunk = data[offset : offset + page.limit]
        items = [ConversationThread(**item) for item in chunk]
        next_offset = offset + len(items)
        return ConversationPageResult(
            items=items,
            next_cursor=str(next_offset) if next_offset < len(data) else None,
            has_more=next_offset < len(data),
        )

