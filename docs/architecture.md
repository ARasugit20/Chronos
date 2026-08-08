# Architecture

## Pipeline stages

1. **Ingest** — Celery beat pulls Finnhub or mock news/sports/macro sources every 5 minutes.
2. **Dedup** — SHA256 fingerprint; Redis SET (48h TTL) then PostgreSQL unique constraint.
3. **Theme map** — Regex match against seeded `theme_mappings` (human-approved patterns).
4. **Regime tag** — Rule-based `RegimeTagger` labels event + macro priors (oil/geo, yields, rotation, seasonality).
5. **Score** — `RulesScorer` by default; `LightGBMScorer` after enough resolved outcomes.
6. **Calibrate** — Fitted isotonic regression when enough outcomes exist; shrinkage fallback otherwise.
7. **Edge estimate** — Theme-level expected return/odds from resolved history with shrinkage fallback.
8. **Allocate** — Half-Kelly (or 1/3 Kelly in high-uncertainty regimes) with 8% ticker / 25% sector caps; skip below $10.
9. **Lead rank** — `LeadRanker` computes `rank_score = EV / risk`, clusters duplicate headlines, enforces top-K/day.
10. **Recommend** — Paper recommendation with thesis, invalidate_if, regime, rank_score, and audit id.
11. **Resolve** — Hourly job for approved expired recs; entry/exit prices fetched at signal and expiry timestamps; Brier component stored.
12. **Profit analytics** — `/api/v1/outcome-metrics` reports expectancy, profit factor, and breakdowns by theme/regime.

## Quant validity notes

- Outcome resolution uses **timestamped prices** at signal creation and recommendation expiry.
- Retraining uses a **time-ordered train/calibrate/test split** to reduce leakage.
- `/api/v1/outcome-metrics` reports realized outcome quality; it does not replay historical point-in-time features/prices.
- Paper trading can auto-approve a shadow track so outcomes remain resolvable without manual clicks.
- Portfolio exposure is computed from open buy/paper_buy recommendations against configured cash and cap limits.
- **P2 deferred:** full point-in-time replay engine and external notify/webhook delivery gated on OOS Brier + positive expectancy.

## Data model

```
Event 1──* Signal 1──0..1 Recommendation 1──0..1 Outcome
ThemeMapping (standalone seed table)
```

Recommendation lead fields (nullable for legacy rows): `theme_bucket`, `regime`, `regime_flags`, `calibrated_p`, `thesis`, `invalidate_if`, `evidence`, `rank_score`, `kelly_half_pct`, `adjustment_reason`.

## Scalability notes

- **Read path**: composite indexes on `(suppressed, created_at)` and `(status, created_at)`.
- **Write path**: dedup fast path in Redis avoids hot-row contention on `events`.
- **Workers**: Celery tasks are idempotent on fingerprint; scale workers horizontally.
- **API**: `offset`/`limit` on list endpoints; `X-Request-ID` on all HTTP responses.

## Observability

- structlog JSON on pipeline steps
- Prometheus `/metrics` on FastAPI
- Health check: DB, Redis, worker heartbeat key
