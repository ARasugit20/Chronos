# Roadmap

## Completed

- [x] JWT auth on mutating endpoints
- [x] LightGBM scorer + feature engineering
- [x] Fitted isotonic calibration (with fallback)
- [x] Embedding theme fallback (hash fallback when ST unavailable)
- [x] Polygon price feed with mock fallback
- [x] Configurable Kelly odds + sector/drawdown guards
- [x] Cursor pagination + Redis rate limiting
- [x] Expanded Prometheus metrics
- [x] Demo seed (`make seed-demo`)
- [x] E2E smoke tests
- [x] Signal quality guardrails
- [x] Dark/light theme toggle
- [x] WebSocket signal feed
- [x] CI coverage + type-check jobs
- [x] Render deploy blueprint + live deploy smoke checks
- [x] Timestamp-correct outcome resolution
- [x] Temporal train/calibrate/test retrain split
- [x] Outcome metrics API + research dashboard
- [x] Alembic migration validation in CI
- [x] Portfolio exposure API + risk dashboard panel
- [x] Point-in-time rules scoring (`as_of`) for replay-safe recency
- [x] Drawdown guard wired into live allocation path
- [x] RegimeTagger + lead schema (thesis, invalidate_if, rank_score, regime)
- [x] EdgeModel with theme-history shrinkage
- [x] LeadRanker (EV/risk, cluster dedupe, top-K/day)
- [x] Regime-aware allocator delever + adjustment_reason
- [x] Profit-quality analytics (expectancy, profit factor, theme/regime breakdowns)

## Next

- [ ] Point-in-time historical replay backtest engine (credibility gate for notify/high-quality badge)
- [ ] Optional webhook/email delivery stub behind replay gates
- [ ] Demo GIF in README
- [ ] pgvector for production embeddings
- [ ] Horizontal Celery autoscaling
- [ ] DB user table + OAuth
