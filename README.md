# Chronos (invest-agent)

[![CI](https://github.com/ARasugit20/Chronos/actions/workflows/ci.yml/badge.svg)](https://github.com/ARasugit20/Chronos/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Event-driven quant research agent** that ingests news/sports/macro events, maps them to ticker themes, scores probability, sizes positions with Kelly caps, and surfaces buy/skip recommendations with full audit provenance.

Repository: [https://github.com/ARasugit20/Chronos](https://github.com/ARasugit20/Chronos)

---

## Why this project (recruiter snapshot)

| Highlight | What it demonstrates |
|-----------|-------------------|
| **Full-stack ownership** | FastAPI + Celery + PostgreSQL + Redis + React dashboard |
| **ML-ready pipeline** | Rules scorer today, LightGBM + isotonic calibration stubs with outcome loop |
| **Risk controls** | Half-Kelly sizing, per-ticker and sector caps, signal suppression |
| **Production patterns** | Docker Compose, Alembic migrations, Prometheus metrics, structlog JSON |
| **Data integrity** | Redis + DB dedup, cascade FKs, audit trail API |

---

## Architecture

```mermaid
flowchart LR
  subgraph ingest
    A[Sports/Macro/News mocks] --> B[Celery Beat 5m]
  end
  B --> C[Dedup Redis+PG]
  C --> D[Theme regex map]
  D --> E[Score + Calibrate]
  E --> F[Kelly Allocator]
  F --> G[Recommendation]
  G --> H[React Dashboard]
  G --> I[Outcome Resolver]
  I --> J[Brier feedback]
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Pydantic v2, SQLAlchemy 2 async |
| Jobs | Celery 5 + Redis 7 |
| DB | PostgreSQL 16, Alembic |
| Frontend | Vite, React 18, TypeScript, TanStack Query, Tailwind |
| Ops | Docker Compose, Prometheus instrumentator, GitHub Actions CI |

---

## Quick start

```bash
cp .env.example .env   # optional local overrides
make up
make migrate
make seed
```

| Service | URL |
|---------|-----|
| API health | http://localhost:8000/api/v1/health |
| OpenAPI docs | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |
| Metrics | http://localhost:8000/metrics |

---

## API overview

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/events/ingest` | Ingest event (dedup) |
| `GET` | `/api/v1/signals/live` | Live signals (`offset`, `limit`) |
| `GET` | `/api/v1/recommendations` | List recommendations |
| `POST` | `/api/v1/recommendations/{id}/approve` | Approve trade signal |
| `GET` | `/api/v1/audit/{id}` | Full provenance chain |

See [docs/api.md](docs/api.md) and [docs/architecture.md](docs/architecture.md).

---

## Scalability roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned upgrades: JWT auth, embedding-based theme match, real price feeds, horizontal Celery workers, and fitted calibration.

---

## Known Limitations

1. Price data uses mock random walk — replace `PRICE_SOURCE=mock` with `polygon` or `yahoo` for real data
2. LightGBMScorer is a stub — model trains only after sufficient Outcome records exist (minimum 50 recommended)
3. Calibration uses fixed 0.85 shrinkage — replace with fitted IsotonicRegression once outcomes accumulate
4. Theme mapping uses simple regex — upgrade to embedding similarity for better event matching at scale
5. No authentication on API endpoints — add JWT before any public deployment
6. Telegram adapter sends to single chat_id — multi-user requires subscription model
7. Kelly sizing assumes simplified b=1.0 odds — replace with actual expected return from event study data

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
