# WHY: Prometheus metrics for pipeline observability.

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

events_ingested_total = Counter(
    "events_ingested_total",
    "Events ingested",
    ["source", "is_duplicate"],
)
signals_generated_total = Counter(
    "signals_generated_total",
    "Signals generated",
    ["ticker", "bucket"],
)
recommendations_actioned_total = Counter(
    "recommendations_actioned_total",
    "Recommendation actions",
    ["action"],
)
pipeline_duration_seconds = Histogram(
    "pipeline_duration_seconds",
    "Pipeline ingest duration",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
brier_score_gauge = Gauge("brier_score_gauge", "Latest mean Brier component")
