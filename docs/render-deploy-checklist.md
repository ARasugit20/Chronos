# Render Deploy Checklist

Use this checklist when turning Chronos from a local demo into a live Finnhub-backed Render deployment.

## 1. Blueprint Services

Create the stack from `render.yaml` as a Render Blueprint. It should create:

| Service | Expected name | Purpose |
|---------|---------------|---------|
| API | `chronos-api` | FastAPI app, health endpoint, REST API |
| Worker | `chronos-worker` | Celery worker + Beat scheduler |
| Redis | `chronos-redis` | Broker, dedup cache, WebSocket pub/sub |
| Postgres | `chronos-db` | Events, signals, recommendations, outcomes |
| Frontend | `chronos-frontend` | Static React dashboard |

## 2. Required Secrets

Set these in the Render API and worker services before the first production deploy:

| Key | Required | Notes |
|-----|----------|-------|
| `NEWS_SOURCE` | yes | Must be `finnhub` for live news |
| `NEWS_API_KEY` | yes | Free key from <https://finnhub.io/register> |
| `SECRET_KEY` | yes | Render can generate it for the API service |
| `ADMIN_PASSWORD` | yes | Strong password for `/api/v1/auth/token` |
| `PAPER_TRADING_MODE` | recommended | Keep `true` until signal quality is validated |
| `PRICE_SOURCE` | recommended | Keep `mock` until a real price key is configured |

## 3. First Deploy Verification

After deploy, check API health:

```bash
export CHRONOS_API_URL=https://chronos-api.onrender.com
make check-live
```

For a stricter live-news check:

```bash
python3 scripts/check_live_deploy.py "$CHRONOS_API_URL" --require-live-news
```

The `/api/v1/health` payload should show:

| Field | Expected value |
|-------|----------------|
| `news_source` | `finnhub` |
| `mock_news_mode` | `false` |
| `live_news_ready` | `true` |
| `paper_trading_mode` | `true` initially |

## 4. Signal Verification

Celery Beat runs ingestion every 5 minutes. After the first run:

```bash
python3 scripts/check_live_deploy.py "$CHRONOS_API_URL" --require-live-news --require-signals
```

If no signals appear, inspect:

- `chronos-worker` logs for Finnhub API errors
- `NEWS_API_KEY` on both API and worker services
- `NEWS_SOURCE=finnhub` on both API and worker services
- `/api/v1/health` alerts for `news_api_key_missing`, `worker_heartbeat_missing`, or `ingest_stale`

## 5. Frontend Verification

Open `https://chronos-frontend.onrender.com` and confirm:

- The dashboard loads without a blank page
- API calls target the Render API host
- Login works with `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- Live signals and recommendations render after ingestion has run

## 6. README Badges

Once Render assigns the final service hostnames, update the README badges if they differ from:

- `https://chronos-api.onrender.com/api/v1/health`
- `https://chronos-frontend.onrender.com`
