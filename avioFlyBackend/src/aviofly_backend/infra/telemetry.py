from __future__ import annotations

from dataclasses import dataclass, field

from ..core.interfaces import Telemetry


@dataclass
class ConsoleTelemetry(Telemetry):
    events: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    latencies: list[tuple[str, int, dict[str, str]]] = field(default_factory=list)

    def track_event(self, name: str, properties: dict[str, str] | None = None) -> None:
        properties = properties or {}
        self.events.append((name, properties))
        print(f"[telemetry] event={name} props={properties}")

    def track_latency(self, name: str, milliseconds: int, properties: dict[str, str] | None = None) -> None:
        properties = properties or {}
        self.latencies.append((name, milliseconds, properties))
        print(f"[telemetry] latency={name} ms={milliseconds} props={properties}")

