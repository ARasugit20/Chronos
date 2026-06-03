# Roadmap

## Near term (portfolio / interview demo)

- [x] End-to-end mock pipeline with dashboard
- [x] GitHub Actions CI
- [x] DB performance indexes
- [ ] JWT auth middleware
- [ ] `.env` secrets via Docker secrets / GitHub Actions vars

## Scalability

- [ ] Embedding-based theme matching (pgvector or external vector DB)
- [ ] Partition `events` by month
- [ ] Celery queue per source type (sports / macro / news)
- [ ] Read replicas for signal feed API
- [ ] Rate limiting (Redis token bucket)

## Functionality

- [ ] Polygon / Yahoo price adapters
- [ ] LightGBM training on `Outcome` table (min 50 samples)
- [ ] Fitted isotonic calibration per `event_type`
- [ ] Multi-user Telegram subscriptions
- [ ] Backtest mode (historical event replay)

## Recruiter-facing polish

- [x] Architecture diagram in README
- [x] CI badge
- [ ] Demo GIF in README
- [ ] Deploy preview (Railway / Render) with health URL in README
