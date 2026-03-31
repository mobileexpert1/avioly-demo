from __future__ import annotations

from dataclasses import dataclass, field

from ..core.interfaces import Telemetry


@dataclass
class InMemoryTelemetry(Telemetry):
    events: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    latencies: list[tuple[str, int, dict[str, str]]] = field(default_factory=list)

    def track_event(self, name: str, properties: dict[str, str] | None = None) -> None:
        # This stays intentionally lightweight so it can be replaced with real observability later.
        self.events.append((name, properties or {}))

    def track_latency(self, name: str, milliseconds: int, properties: dict[str, str] | None = None) -> None:
        self.latencies.append((name, milliseconds, properties or {}))
