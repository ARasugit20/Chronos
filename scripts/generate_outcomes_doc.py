#!/usr/bin/env python3
"""Generate docs/outcomes.md and calibration PNG from resolved prediction records."""

from __future__ import annotations

import json
import struct
import zlib
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "backend" / "app" / "data" / "resolved_predictions.json"
OUT_PATH = REPO_ROOT / "docs" / "outcomes.md"
PNG_PATH = REPO_ROOT / "docs" / "assets" / "calibration_reliability.png"

BUCKET_ORDER = ("low", "medium", "high")
BUCKET_COLORS = {
    "low": (99, 102, 241),
    "medium": (14, 165, 233),
    "high": (5, 150, 105),
}

# 6x8 bitmap glyphs: each row is 6 bits wide (MSB left).
FONT: dict[str, tuple[str, ...]] = {
    " ": ("000000", "000000", "000000", "000000", "000000", "000000", "000000", "000000"),
    "(": ("001110", "010000", "100000", "100000", "100000", "010000", "001110", "000000"),
    ")": ("111000", "000100", "000010", "000010", "000010", "000100", "111000", "000000"),
    "-": ("000000", "000000", "000000", "111111", "111111", "000000", "000000", "000000"),
    ".": ("000000", "000000", "000000", "000000", "000000", "011000", "011000", "000000"),
    "/": ("000011", "000110", "001100", "011000", "110000", "100000", "000000", "000000"),
    "0": ("011110", "100001", "100011", "101101", "110001", "100001", "011110", "000000"),
    "1": ("001100", "011100", "001100", "001100", "001100", "001100", "011110", "000000"),
    "2": ("011110", "100001", "000001", "000110", "011000", "100000", "111111", "000000"),
    "3": ("111110", "000001", "000001", "011110", "000001", "000001", "111110", "000000"),
    "4": ("000110", "001110", "010110", "100110", "111111", "000110", "000110", "000000"),
    "5": ("111111", "100000", "111110", "000001", "000001", "100001", "011110", "000000"),
    "6": ("001110", "010000", "100000", "111110", "100001", "100001", "011110", "000000"),
    "7": ("111111", "000001", "000010", "000100", "001000", "010000", "010000", "000000"),
    "8": ("011110", "100001", "100001", "011110", "100001", "100001", "011110", "000000"),
    "9": ("011110", "100001", "100001", "011111", "000001", "000010", "011100", "000000"),
    "=": ("000000", "111111", "000000", "111111", "000000", "000000", "000000", "000000"),
    "A": ("011110", "100001", "100001", "111111", "100001", "100001", "100001", "000000"),
    "B": ("111110", "100001", "100001", "111110", "100001", "100001", "111110", "000000"),
    "C": ("011110", "100001", "100000", "100000", "100000", "100001", "011110", "000000"),
    "D": ("111100", "100010", "100001", "100001", "100001", "100010", "111100", "000000"),
    "E": ("111111", "100000", "100000", "111110", "100000", "100000", "111111", "000000"),
    "F": ("111111", "100000", "100000", "111110", "100000", "100000", "100000", "000000"),
    "G": ("011110", "100001", "100000", "100111", "100001", "100001", "011110", "000000"),
    "H": ("100001", "100001", "100001", "111111", "100001", "100001", "100001", "000000"),
    "I": ("011110", "001100", "001100", "001100", "001100", "001100", "011110", "000000"),
    "K": ("100001", "100010", "100100", "111000", "100100", "100010", "100001", "000000"),
    "L": ("100000", "100000", "100000", "100000", "100000", "100000", "111111", "000000"),
    "M": ("100001", "110011", "101101", "100001", "100001", "100001", "100001", "000000"),
    "N": ("100001", "110001", "101001", "100101", "100011", "100001", "100001", "000000"),
    "O": ("011110", "100001", "100001", "100001", "100001", "100001", "011110", "000000"),
    "P": ("111110", "100001", "100001", "111110", "100000", "100000", "100000", "000000"),
    "R": ("111110", "100001", "100001", "111110", "100100", "100010", "100001", "000000"),
    "S": ("011110", "100001", "100000", "011110", "000001", "100001", "011110", "000000"),
    "T": ("111111", "001100", "001100", "001100", "001100", "001100", "001100", "000000"),
    "V": ("100001", "100001", "100001", "100001", "100001", "010010", "001100", "000000"),
    "Y": ("100001", "100001", "010010", "001100", "001100", "001100", "001100", "000000"),
    "a": ("000000", "000000", "011110", "000001", "011111", "100001", "011111", "000000"),
    "b": ("100000", "100000", "101110", "110001", "100001", "100001", "101110", "000000"),
    "c": ("000000", "000000", "011110", "100000", "100000", "100000", "011110", "000000"),
    "d": ("000001", "000001", "011101", "100011", "100001", "100001", "011111", "000000"),
    "e": ("000000", "000000", "011110", "100001", "111111", "100000", "011110", "000000"),
    "g": ("000000", "000000", "011111", "100001", "011111", "000001", "011110", "000000"),
    "h": ("100000", "100000", "101110", "110001", "100001", "100001", "100001", "000000"),
    "i": ("001100", "000000", "011100", "001100", "001100", "001100", "011110", "000000"),
    "k": ("100000", "100000", "100101", "100110", "111000", "100110", "100101", "000000"),
    "l": ("011100", "001100", "001100", "001100", "001100", "001100", "011110", "000000"),
    "m": ("000000", "000000", "110110", "101101", "101101", "100001", "100001", "000000"),
    "n": ("000000", "000000", "101110", "110001", "100001", "100001", "100001", "000000"),
    "o": ("000000", "000000", "011110", "100001", "100001", "100001", "011110", "000000"),
    "p": ("000000", "000000", "101110", "110001", "101110", "100000", "100000", "000000"),
    "r": ("000000", "000000", "101110", "110001", "100000", "100000", "100000", "000000"),
    "s": ("000000", "000000", "011110", "100000", "011110", "000001", "111110", "000000"),
    "t": ("001100", "001100", "111111", "001100", "001100", "001100", "000110", "000000"),
    "u": ("000000", "000000", "100001", "100001", "100001", "100011", "011101", "000000"),
    "v": ("000000", "000000", "100001", "100001", "100001", "010010", "001100", "000000"),
    "y": ("000000", "000000", "100001", "100001", "011111", "000001", "011110", "000000"),
}


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


class Canvas:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        self.fill(255, 255, 255)

    def _idx(self, x: int, y: int) -> int:
        return (y * self.width + x) * 3

    def set_pixel(self, x: int, y: int, rgb: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            self.pixels[i : i + 3] = bytes(rgb)

    def fill(self, r: int, g: int, b: int) -> None:
        row = bytes((r, g, b)) * self.width
        self.pixels[:] = row * self.height

    def fill_rect(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        rgb: tuple[int, int, int],
    ) -> None:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set_pixel(x, y, rgb)

    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        rgb: tuple[int, int, int],
        *,
        dash: int = 0,
    ) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        step = 0
        while True:
            if dash == 0 or (step // dash) % 2 == 0:
                self.set_pixel(x0, y0, rgb)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
            step += 1

    def draw_circle(
        self,
        cx: int,
        cy: int,
        radius: int,
        fill: tuple[int, int, int],
        outline: tuple[int, int, int] | None = None,
    ) -> None:
        r2 = radius * radius
        for y in range(cy - radius - 1, cy + radius + 2):
            for x in range(cx - radius - 1, cx + radius + 2):
                dist2 = (x - cx) ** 2 + (y - cy) ** 2
                if dist2 <= r2:
                    self.set_pixel(x, y, fill)
                elif outline and radius**2 < dist2 <= (radius + 1) ** 2:
                    self.set_pixel(x, y, outline)

    def draw_text(self, x: int, y: int, text: str, rgb: tuple[int, int, int]) -> None:
        cursor = x
        for char in text:
            glyph = FONT.get(char, FONT[" "])
            for row_idx, row in enumerate(glyph):
                for col_idx, bit in enumerate(row):
                    if bit == "1":
                        self.set_pixel(cursor + col_idx, y + row_idx, rgb)
            cursor += 7


def encode_png(width: int, height: int, rgb_bytes: bytes) -> bytes:
    rows = []
    stride = width * 3
    for y in range(height):
        rows.append(b"\x00" + rgb_bytes[y * stride : (y + 1) * stride])
    compressed = zlib.compress(b"".join(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def render_reliability_png(reliability: dict[str, dict[str, float]]) -> bytes:
    width, height = 520, 420
    margin = 60
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin
    canvas = Canvas(width, height)

    axis = (51, 65, 85)
    muted = (148, 163, 184)
    title = (15, 23, 42)
    caption = (180, 83, 9)

    def scale_x(value: float) -> int:
        return margin + round(value * plot_width)

    def scale_y(value: float) -> int:
        return height - margin - round(value * plot_height)

    canvas.draw_line(margin, height - margin, width - margin, height - margin, axis)
    canvas.draw_line(margin, margin, margin, height - margin, axis)
    canvas.draw_line(
        scale_x(0.0),
        scale_y(0.0),
        scale_x(1.0),
        scale_y(1.0),
        muted,
        dash=6,
    )

    canvas.draw_text(130, 12, "Calibration reliability (mock track)", title)
    canvas.draw_text(145, 30, "Not live P&L - mock price track", caption)
    canvas.draw_text(170, height - 20, "Mean predicted probability", muted)
    canvas.draw_text(12, 200, "Observed hit rate", muted)

    for bucket in BUCKET_ORDER:
        stats = reliability.get(bucket)
        if not stats:
            continue
        cx = scale_x(stats["mean_predicted"])
        cy = scale_y(stats["observed_hit_rate"])
        radius = 8 + min(int(stats["samples"]), 12)
        color = BUCKET_COLORS[bucket]
        canvas.draw_circle(cx, cy, radius, color, outline=(255, 255, 255))
        label = f"{bucket} (n={int(stats['samples'])})"
        canvas.draw_text(cx - len(label) * 3, cy - radius - 14, label, title)

    return encode_png(width, height, bytes(canvas.pixels))


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

![Calibration reliability diagram on mock-track resolver outcomes](assets/calibration_reliability.png)

| Bucket | Samples | Mean predicted | Observed hit rate | Calibration gap |
|--------|--------:|---------------:|------------------:|----------------:|
{bucket_rows}

## Notes

- **Brier score** averages `(calibrated_p - outcome)^2` over resolved predictions only.
- **Skip/abstain rate** is the share of pipeline decisions that did not promote a lead
  (`action=skip`), including confidence/EV guards and daily-cap displacement.
- Records are point-in-time resolver exports on the mock price track; they measure
  calibration quality, not trading P&L.
- Regenerate this page and the PNG with `python3 scripts/generate_outcomes_doc.py`.
"""


def main() -> None:
    records = load_records()
    metrics = compute_metrics(records)
    reliability = compute_reliability_buckets(records)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PNG_PATH.write_bytes(render_reliability_png(reliability))
    OUT_PATH.write_text(
        render_markdown(metrics, reliability, generated_at=generated_at),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {PNG_PATH}")


if __name__ == "__main__":
    main()
