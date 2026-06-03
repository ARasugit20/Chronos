# Data Model

## Event

| Column | Type | Notes |
|--------|------|-------|
| `fingerprint_hash` | string, unique | SHA256 dedup key |
| `metadata_json` | JSONB | Optional price hints for resolver |

## Signal

| Column | Type | Notes |
|--------|------|-------|
| `probability_calibrated` | float | Post-calibration score |
| `suppressed` | bool | Below confidence threshold |

## Recommendation

| Column | Type | Notes |
|--------|------|-------|
| `amount_usd` | Numeric(12,2) | 0 when action=skip |
| `status` | enum-like string | pending → approved/skipped → resolved |

## Outcome

| Column | Type | Notes |
|--------|------|-------|
| `brier_component` | float | `(prob_calibrated - hit)^2` for model feedback |
| `hit_boolean` | bool | Positive return on buy action |

Relationships use `ON DELETE CASCADE` from Event → Signal → Recommendation → Outcome.
