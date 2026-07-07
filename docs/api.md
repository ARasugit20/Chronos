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
| `offset` | `0` | Pagination offset |

## Recommendations

### `GET /api/v1/recommendations`

| Query | Default | Description |
|-------|---------|-------------|
| `status` | `pending` | Filter by status |
| `limit` | `10` | Page size |
| `offset` | `0` | Pagination offset |

### `POST /api/v1/recommendations/{id}/approve`

Sets `status=approved`.

### `POST /api/v1/recommendations/{id}/skip`

Sets `status=skipped`.

## Audit

### `GET /api/v1/audit/{recommendation_id}`

Returns recommendation, signal, event, and outcome (if resolved).

## Research metrics

### `GET /api/v1/outcome-metrics`

Returns **resolved outcome metrics** for model-quality monitoring:

- hit rate and mean Brier score
- precision by ticker (minimum 3 samples)
- confidence-bucket reliability (predicted vs observed)
- `ml_ready` when enough outcomes exist for retraining

This endpoint reports realized outcomes only. It is **not** a point-in-time historical replay engine.

### `GET /api/v1/backtest` (deprecated)

Compatibility alias for `/api/v1/outcome-metrics`.

## Health & metrics

- `GET /api/v1/health` — DB/Redis/worker status plus deploy readiness flags (`live_news_ready`, `live_price_ready`, etc.)
- `GET /metrics` — Prometheus exposition
