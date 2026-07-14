# Architecture

## Pipeline stages

1. **Ingest** — Celery beat pulls Finnhub or mock news/sports/macro sources every 5 minutes.
2. **Dedup** — SHA256 fingerprint; Redis SET (48h TTL) then PostgreSQL unique constraint.
3. **Theme map** — Regex match against seeded `theme_mappings` (human-approved patterns).
4. **Score** — `RulesScorer` by default; `LightGBMScorer` after enough resolved outcomes.
5. **Calibrate** — Fitted isotonic regression when enough outcomes exist; shrinkage fallback otherwise.
6. **Allocate** — Half-Kelly with 8% ticker / 25% sector caps; skip below $10.
7. **Recommend** — Pending or auto-approved paper recommendation with disclaimer and expiry horizon.
8. **Resolve** — Hourly job for approved expired recs; entry/exit prices fetched at signal and expiry timestamps; Brier component stored.

## Quant validity notes

- Outcome resolution uses **timestamped prices** at signal creation and recommendation expiry.
- Retraining uses a **time-ordered train/calibrate/test split** to reduce leakage.
- `/api/v1/outcome-metrics` reports realized outcome quality; it does not replay historical point-in-time features/prices.
- Paper trading can auto-approve a shadow track so outcomes remain resolvable without manual clicks.
- Portfolio exposure is computed from open buy/paper_buy recommendations against configured cash and cap limits.

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
