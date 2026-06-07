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
ingest_stale_gauge = Gauge("ingest_stale", "1 if ingestion is stale")
worker_heartbeat_gauge = Gauge("worker_heartbeat", "1 if worker heartbeat present")
mock_price_mode_gauge = Gauge("mock_price_mode", "1 if using mock prices")
mock_news_mode_gauge = Gauge("mock_news_mode", "1 if using mock news")
