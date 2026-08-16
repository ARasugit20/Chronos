from datetime import UTC, datetime
from typing import ClassVar, Protocol, TypedDict


class RawEventDict(TypedDict):
    source: str
    event_type: str
    title: str
    occurred_at: datetime
    metadata: dict


class EventSource(Protocol):
    async def fetch(self) -> list[RawEventDict]:
        """Returns list of dicts with keys: source, event_type, title, occurred_at, metadata"""
        ...


class SportsMockSource:
    _EVENTS: ClassVar[list[str]] = [
        "FIFA World Cup 2026 — Host cities confirmed",
        "NBA Finals — Game 7 primetime",
        "Super Bowl LX — 2 weeks out",
        "Olympics 2028 — LA venue announcement",
    ]

    async def fetch(self) -> list[RawEventDict]:
        idx = datetime.now(UTC).date().toordinal() % len(self._EVENTS)
        return [
            {
                "source": "sports_mock",
                "event_type": "sports",
                "title": self._EVENTS[idx],
                "occurred_at": datetime.now(UTC),
                "metadata": {"data_source": "mock"},
            }
        ]
