# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `/docs` (Swagger UI)

## Events

### `POST /api/v1/events/ingest`

```json
{
  "source": "manual",
  "event_type": "sports",
  "title": "FIFA World Cup 2026 test",
  "occurred_at": "2026-06-02T00:00:00Z",
  "metadata": {}
}
```

| Status | Meaning |
|--------|---------|
| 201 | New event processed |
| 200 | Duplicate fingerprint |

## Signals

### `GET /api/v1/signals/live`

| Query | Default | Description |
|-------|---------|-------------|
| `suppressed` | `false` | Include suppressed signals |
| `limit` | `20` | Page size (max 100) |
| `cursor` | — | Cursor UUID for next page |

## Recommendations

### `GET /api/v1/recommendations`

Returns leads sorted by `rank_score` (desc). Each recommendation includes:

| Field | Description |
|-------|-------------|
| `theme_bucket` | Investable theme bucket (e.g. `ENERGY_SHOCK`) |
| `regime` | Primary regime enum |
| `regime_flags` | Composable macro flags |
| `calibrated_p` | Calibrated probability |
| `thesis` | 1–2 sentence lead thesis |
| `invalidate_if` | Rule string for invalidation |
| `evidence` | Clustered headline evidence list |
| `rank_score` | Expected value / risk |
| `kelly_half_pct` | Half-Kelly fraction used |
| `adjustment_reason` | Sizing/regime adjustment notes |

| Query | Default | Description |
|-------|---------|-------------|
| `status` | `pending` | Filter by status |
| `limit` | `50` | Page size |
| `cursor` | — | Cursor UUID for next page |

### `POST /api/v1/recommendations/{id}/approve`

Sets `status=approved`.

### `POST /api/v1/recommendations/{id}/skip`

Sets `status=skipped`.

## Audit

### `GET /api/v1/audit/{recommendation_id}`

Returns recommendation (with lead fields), signal, event, and outcome (if resolved).

## Research metrics

### `GET /api/v1/outcome-metrics`

Returns **resolved outcome metrics** for model-quality monitoring:

- hit rate and mean Brier score
- precision by ticker (minimum 3 samples)
- confidence-bucket reliability (predicted vs observed)
- expectancy, profit factor, mean win/loss
- breakdowns by confidence bucket, theme bucket, and regime
- sector contribution totals
- `ml_ready` when enough outcomes exist for retraining

This endpoint reports realized outcomes only. It is **not** a point-in-time historical replay engine.

### `GET /api/v1/backtest` (deprecated)

Compatibility alias for `/api/v1/outcome-metrics`.

## Portfolio

### `GET /api/v1/portfolio`

Returns cash, deployment, ticker/sector exposure, and cap utilization for open buy/paper_buy recommendations.

### `POST /api/v1/historical-replay`

Replay caller-supplied point-in-time observations with explicit costs. Separate from outcome metrics.

## Health & metrics

- `GET /api/v1/health` — DB/Redis/worker status plus deploy readiness flags (`live_news_ready`, `live_price_ready`, etc.)
- `GET /metrics` — Prometheus exposition

## Configuration (regime-aware leads)

| Env var | Default | Description |
|---------|---------|-------------|
| `PAPER_TRADING_MODE` | `true` | Force paper-only recommendations |
| `MAX_DAILY_LEADS` | `5` | Top-K promoted leads per day |
| `CLUSTER_WINDOW_HOURS` | `6` | Same-ticker headline cluster window |
| `MIN_EV_USD` | `0.0` | Minimum expected value to promote |
| `EDGE_MIN_SAMPLES` | `20` | Theme history threshold before shrinkage relaxes |
| `DEFAULT_RANGE_ROTATION` | `true` | Aug-2026 range/rotation prior |
