from datetime import date

from app.pipeline.dedup import compute_provider_fingerprint, resolve_fingerprint


def test_provider_fingerprint_from_id() -> None:
    fp1 = compute_provider_fingerprint("12345")
    fp2 = compute_provider_fingerprint("12345")
    fp3 = compute_provider_fingerprint("99999")
    assert fp1 == fp2
    assert fp1 != fp3


def test_resolve_fingerprint_prefers_provider_id() -> None:
    fp = resolve_fingerprint(
        source="finnhub",
        event_type="news",
        title="Same headline different day",
        occurred_date=date(2026, 6, 7),
        metadata={"provider_id": "abc-123", "url": "https://example.com/a"},
    )
    fp2 = resolve_fingerprint(
        source="finnhub",
        event_type="news",
        title="Different headline",
        occurred_date=date(2026, 6, 8),
        metadata={"provider_id": "abc-123"},
    )
    assert fp == fp2


def test_resolve_fingerprint_falls_back_to_title() -> None:
    fp = resolve_fingerprint(
        source="manual",
        event_type="news",
        title="Unique event",
        occurred_date=date(2026, 6, 7),
        metadata={},
    )
    assert len(fp) == 64
