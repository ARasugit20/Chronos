from datetime import UTC, datetime
from typing import ClassVar

from app.adapters.sports_source import EventSource, RawEventDict


class MacroMockSource:
    _EVENTS: ClassVar[list[str]] = [
        "Federal Reserve holds rates — dovish language",
        "CPI print: 2.8% YoY — below expectations",
        "Q2 GDP: +2.1% — in line",
    ]

    async def fetch(self) -> list[RawEventDict]:
        idx = datetime.now(UTC).hour % len(self._EVENTS)
        return [
            {
                "source": "macro_mock",
                "event_type": "macro",
                "title": self._EVENTS[idx],
                "occurred_at": datetime.now(UTC),
                "metadata": {"data_source": "mock"},
            }
        ]


def get_macro_source() -> EventSource:
    return MacroMockSource()
