from __future__ import annotations

from dataclasses import dataclass, field

from ..core.interfaces import UsageTracker
from ..core.models import UsageRecord


@dataclass
class InMemoryUsageStore(UsageTracker):
    records: dict[str, UsageRecord] = field(default_factory=dict)

    def record(self, usage: UsageRecord) -> None:
        self.records[usage.conversation_id] = usage

    def totals_for_conversation(self, conversation_id: str) -> UsageRecord:
        return self.records.get(conversation_id, UsageRecord(request_id="", conversation_id=conversation_id))

