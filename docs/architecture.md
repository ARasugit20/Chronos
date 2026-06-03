# Architecture

## Pipeline stages

1. **Ingest** — Celery beat pulls mock sports/macro/news sources every 5 minutes.
2. **Dedup** — SHA256 fingerprint; Redis SET (48h TTL) then PostgreSQL unique constraint.
3. **Theme map** — Regex match against seeded `theme_mappings` (human-approved patterns).
4. **Score** — `RulesScorer` (recency + source trust); `LightGBMScorer` stub for future ML.
5. **Calibrate** — Isotonic shrinkage stub (0.85 toward 0.5).
6. **Allocate** — Half-Kelly with 8% ticker / 25% sector caps; skip below $10.
7. **Recommend** — Pending recommendation with disclaimer and expiry horizon.
8. **Resolve** — Hourly job for approved expired recs; mock prices; Brier component stored.

## Data model

```
Event 1──* Signal 1──0..1 Recommendation 1──0..1 Outcome
ThemeMapping (standalone seed table)
```

## Scalability notes

- **Read path**: composite indexes on `(suppressed, created_at)` and `(status, created_at)`.
- **Write path**: dedup fast path in Redis avoids hot-row contention on `events`.
- **Workers**: Celery tasks are idempotent on fingerprint; scale workers horizontally.
- **API**: `offset`/`limit` on list endpoints; `X-Request-ID` on all HTTP responses.

## Observability

- structlog JSON on pipeline steps
- Prometheus `/metrics` on FastAPI
- Health check: DB, Redis, worker heartbeat key
