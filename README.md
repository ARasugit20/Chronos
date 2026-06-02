# Chronos (invest-agent)

Quant project: invest agent tracks live news and stock trends to give realtime advice on what stock or ETF would be hot right now to buy.

Repository: [https://github.com/ARasugit20/Chronos](https://github.com/ARasugit20/Chronos)

## Quick start

```bash
make up
make migrate
make seed
```

- API: http://localhost:8000/api/v1/health
- UI: http://localhost:3000
- Metrics: http://localhost:8000/metrics

## Known Limitations

1. Price data uses mock random walk — replace `PRICE_SOURCE=mock` with `polygon` or `yahoo` for real data
2. LightGBMScorer is a stub — model trains only after sufficient Outcome records exist (minimum 50 recommended)
3. Calibration uses fixed 0.85 shrinkage — replace with fitted IsotonicRegression once outcomes accumulate
4. Theme mapping uses simple regex — upgrade to embedding similarity for better event matching at scale
5. No authentication on API endpoints — add JWT before any public deployment
6. Telegram adapter sends to single chat_id — multi-user requires subscription model
7. Kelly sizing assumes simplified b=1.0 odds — replace with actual expected return from event study data
