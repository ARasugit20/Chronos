# Runbook

## Commands

- `make up` — start stack
- `make migrate` — apply Alembic migrations
- `make seed` — load theme mappings
- `make seed-demo` — run full demo pipeline for all 5 themes
- `make logs` — tail backend/worker logs

## Key Metrics

| Metric | Meaning | Alert threshold |
|--------|---------|-----------------|
| `events_ingested_total` | Ingest volume by source | sudden drop → worker down |
| `signals_generated_total` | Signals per ticker/bucket | flatline → pipeline stuck |
| `recommendations_actioned_total` | approve/skip counts | — |
| `pipeline_duration_seconds` | ingest latency | p95 > 2s |
| `brier_score_gauge` | model calibration quality | > 0.25 investigate scorer |
| `price_fetches_total` | polygon vs mock ratio | mock-only in prod → check API key |
