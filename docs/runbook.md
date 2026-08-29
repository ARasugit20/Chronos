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

## Incident log

### Orphan signal on clustered headlines (Aug 2026)

**Symptom:** Duplicate headlines for the same ticker created an extra `Signal` row alongside the clustered `Recommendation`, inflating `signals_generated_total` without a matching cluster update.

**Signal:** Prometheus `signals_generated_total{ticker,bucket}` incremented in [`backend/app/services/pipeline_service.py`](../backend/app/services/pipeline_service.py) while structlog emitted no `pipeline.cluster_updated` event — `find_cluster()` ran after signal persistence and was skipped when `cluster.evidence` was null.

**Fix:** [`cfbe5a0`](https://github.com/ARasugit20/Chronos/commit/cfbe5a0) moved `find_cluster()` ahead of signal creation and treats missing evidence as an empty list. Regression test `test_clustered_headlines_merge_without_orphan_signal` in [`backend/tests/test_pipeline_leads.py`](../backend/tests/test_pipeline_leads.py) asserts one recommendation and one signal.

### CI timezone boundary on cluster queries (Aug 2026)

**Symptom:** GitHub Actions ingest tests failed with `asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes` after Ruff UTC cleanup.

**Signal:** Failed run [31966536913](https://github.com/ARasugit20/Chronos/actions/runs/31966536913) blocked `test_pipeline_leads.py::test_clustered_headlines_merge_without_orphan_signal` and related ingest paths.

**Fix:** [`8fdeb64`](https://github.com/ARasugit20/Chronos/commit/8fdeb64) pinned Ruff 0.16.3 and added `utc_now_naive()` in [`backend/app/database.py`](../backend/app/database.py) for DB datetime comparisons in cluster/daily-cap queries. Recovery run [31966788167](https://github.com/ARasugit20/Chronos/actions/runs/31966788167) passed all jobs. Observability remained Prometheus `/metrics` plus structlog JSON only.
