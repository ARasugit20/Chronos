#!/usr/bin/env python3
"""Generate docs/outcomes.md and calibration SVG from resolved prediction records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "backend" / "app" / "data" / "resolved_predictions.json"
OUT_PATH = REPO_ROOT / "docs" / "outcomes.md"
SVG_PATH = REPO_ROOT / "docs" / "assets" / "calibration_reliability.svg"

BUCKET_ORDER = ("low", "medium", "high")


def load_records() -> list[dict]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not records:
        raise ValueError(f"No prediction records found in {DATA_PATH}")
    return records


def confidence_bucket(probability: float) -> str:
    if probability >= 0.65:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


def compute_metrics(records: list[dict]) -> dict[str, float | int]:
    resolved = [row for row in records if row.get("resolved")]
    abstained = [row for row in records if row.get("action") == "skip" or not row.get("resolved")]
    if not resolved:
        raise ValueError("Need at least one resolved prediction to compute outcome metrics")

    briers = [float(row["brier_component"]) for row in resolved]
    hits = sum(1 for row in resolved if row.get("hit_boolean"))
    return {
        "total_predictions": len(records),
        "resolved_predictions": len(resolved),
        "abstained_predictions": len(abstained),
        "abstain_rate": len(abstained) / len(records),
        "mean_brier": sum(briers) / len(briers),
        "hit_rate": hits / len(resolved),
    }


def compute_reliability_buckets(records: list[dict]) -> dict[str, dict[str, float]]:
    resolved = [row for row in records if row.get("resolved")]
    grouped: dict[str, list[tuple[float, int]]] = {name: [] for name in BUCKET_ORDER}

    for row in resolved:
        prob = float(row["probability_calibrated"])
        hit = 1 if row.get("hit_boolean") else 0
        grouped[confidence_bucket(prob)].append((prob, hit))

    reliability: dict[str, dict[str, float]] = {}
    for bucket in BUCKET_ORDER:
        values = grouped[bucket]
        if not values:
            continue
        predicted = sum(prob for prob, _ in values) / len(values)
        observed = sum(hit for _, hit in values) / len(values)
        reliability[bucket] = {
            "samples": float(len(values)),
            "mean_predicted": predicted,
            "observed_hit_rate": observed,
            "calibration_gap": abs(predicted - observed),
        }
    return reliability


def render_reliability_svg(reliability: dict[str, dict[str, float]]) -> str:
    width, height = 520, 420
    margin = 60
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin

    def scale_x(value: float) -> float:
        return margin + value * plot_width

    def scale_y(value: float) -> float:
        return height - margin - value * plot_height

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="Calibration reliability diagram on mock-track resolver outcomes">'
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" '
            f'y2="{height - margin}" stroke="#334155" stroke-width="1.5"/>'
        ),
        (
            f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" '
            f'stroke="#334155" stroke-width="1.5"/>'
        ),
        (
            f'<line x1="{scale_x(0)}" y1="{scale_y(0)}" x2="{scale_x(1)}" y2="{scale_y(1)}" '
            f'stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6 4"/>'
        ),
        (
            f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="sans-serif" '
            f'font-size="16" fill="#0f172a">Calibration reliability (mock track)</text>'
        ),
        (
            f'<text x="{width / 2}" y="{height - 16}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="12" fill="#64748b">Mean predicted probability</text>'
        ),
        (
            f'<text x="18" y="{height / 2}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="12" fill="#64748b" transform="rotate(-90 18 {height / 2})">'
            f"Observed hit rate</text>"
        ),
        (
            f'<text x="{width / 2}" y="46" text-anchor="middle" font-family="sans-serif" '
            f'font-size="11" fill="#b45309">Not live P&amp;L — resolver exports on mock price track</text>'
        ),
    ]

    colors = {"low": "#6366f1", "medium": "#0ea5e9", "high": "#059669"}
    for bucket in BUCKET_ORDER:
        stats = reliability.get(bucket)
        if not stats:
            continue
        x = scale_x(stats["mean_predicted"])
        y = scale_y(stats["observed_hit_rate"])
        radius = 8 + min(stats["samples"], 12)
        lines.extend(
            [
                (
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{colors[bucket]}" '
                    f'fill-opacity="0.85" stroke="#ffffff" stroke-width="1.5"/>'
                ),
                (
                    f'<text x="{x:.1f}" y="{y - radius - 6:.1f}" text-anchor="middle" '
                    f'font-family="sans-serif" font-size="11" fill="#0f172a">'
                    f"{bucket} (n={int(stats['samples'])})</text>"
                ),
            ]
        )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_markdown(
    metrics: dict[str, float | int],
    reliability: dict[str, dict[str, float]],
    *,
    generated_at: str,
) -> str:
    bucket_rows = "\n".join(
        f"| {bucket} | {int(stats['samples'])} | {stats['mean_predicted']:.1%} | "
        f"{stats['observed_hit_rate']:.1%} | {stats['calibration_gap']:.1%} |"
        for bucket in BUCKET_ORDER
        if (stats := reliability.get(bucket))
    )

    return f"""# Chronos outcome metrics

Generated by [`scripts/generate_outcomes_doc.py`](../scripts/generate_outcomes_doc.py) from
[`backend/app/data/resolved_predictions.json`](../backend/app/data/resolved_predictions.json).

Last generated: {generated_at}

## Summary

| Metric | Value |
|--------|------:|
| Resolved predictions (n) | {metrics["resolved_predictions"]} |
| Mean Brier score | {metrics["mean_brier"]:.4f} |
| Resolution accuracy | {metrics["hit_rate"]:.1%} |
| Skip/abstain rate | {metrics["abstain_rate"]:.1%} |
| Total pipeline decisions | {metrics["total_predictions"]} |
| Abstained (skip) decisions | {metrics["abstained_predictions"]} |

## Calibration reliability

![Calibration reliability diagram on mock-track resolver outcomes](assets/calibration_reliability.svg)

| Bucket | Samples | Mean predicted | Observed hit rate | Calibration gap |
|--------|--------:|---------------:|------------------:|----------------:|
{bucket_rows}

## Notes

- **Brier score** averages `(calibrated_p - outcome)^2` over resolved predictions only.
- **Skip/abstain rate** is the share of pipeline decisions that did not promote a lead
  (`action=skip`), including confidence/EV guards and daily-cap displacement.
- Records are point-in-time resolver exports on the mock price track; they measure
  calibration quality, not trading P&L.
- Regenerate this page and the SVG with `python scripts/generate_outcomes_doc.py`.
"""


def main() -> None:
    records = load_records()
    metrics = compute_metrics(records)
    reliability = compute_reliability_buckets(records)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(render_reliability_svg(reliability), encoding="utf-8")
    OUT_PATH.write_text(
        render_markdown(metrics, reliability, generated_at=generated_at),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {SVG_PATH}")


if __name__ == "__main__":
    main()
