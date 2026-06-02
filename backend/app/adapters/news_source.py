from datetime import datetime, timezone

from app.adapters.sports_source import EventSource, RawEventDict


class NewsMockSource:
    _EVENTS = [
        "Marvel film opens to $280M domestic — franchise record",
        "New steel tariff discussion — congressional hearing",
        "AI chip export controls — updated restrictions",
    ]

    async def fetch(self) -> list[RawEventDict]:
        idx = datetime.now(timezone.utc).minute % len(self._EVENTS)
        return [
            {
                "source": "news_mock",
                "event_type": "news",
                "title": self._EVENTS[idx],
                "occurred_at": datetime.now(timezone.utc),
                "metadata": {"data_source": "mock"},
            }
        ]


def get_news_source() -> EventSource:
    return NewsMockSource()
