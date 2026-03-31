from __future__ import annotations

from dataclasses import dataclass, field

from ..core.interfaces import BudgetManager, UsageTracker
from ..core.models import Budget, UsageRecord


@dataclass
class InMemoryUsageTracker(UsageTracker):
    totals: dict[str, UsageRecord] = field(default_factory=dict)

    def record(self, usage: UsageRecord) -> None:
        # Conversation-level totals are enough for the module; finer reporting belongs in the host app.
        current = self.totals.get(usage.conversation_id)
        if current is None:
            self.totals[usage.conversation_id] = usage
            return
        self.totals[usage.conversation_id] = UsageRecord(
            request_id=usage.request_id,
            conversation_id=usage.conversation_id,
            prompt_tokens=current.prompt_tokens + usage.prompt_tokens,
            completion_tokens=current.completion_tokens + usage.completion_tokens,
            cost_usd=current.cost_usd + usage.cost_usd,
            latency_ms=max(current.latency_ms, usage.latency_ms),
            provider=usage.provider or current.provider,
        )

    def totals_for_conversation(self, conversation_id: str) -> UsageRecord:
        return self.totals.get(
            conversation_id,
            UsageRecord(request_id="", conversation_id=conversation_id),
        )


@dataclass(frozen=True)
class SimpleBudgetManager(BudgetManager):
    def allow(self, budget: Budget, usage: UsageRecord) -> bool:
        # Keep the rule set small here; the host can layer stricter policy on top.
        if budget.max_tokens is not None and (usage.prompt_tokens + usage.completion_tokens) > budget.max_tokens:
            return False
        if budget.max_cost_usd is not None and usage.cost_usd > budget.max_cost_usd:
            return False
        return True
