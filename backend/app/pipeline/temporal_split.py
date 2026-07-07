# WHY: Time-ordered train/calibrate/test splits to prevent leakage in ML retraining.

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class TemporalSplit:
    train: list[T]
    calibrate: list[T]
    test: list[T]


def split_by_time(
    rows: list[T],
    *,
    train_ratio: float = 0.70,
    calibrate_ratio: float = 0.15,
    sort_key,
) -> TemporalSplit:
    if not rows:
        return TemporalSplit(train=[], calibrate=[], test=[])

    ordered = sorted(rows, key=sort_key)
    total = len(ordered)
    train_end = max(1, int(total * train_ratio)) if total >= 3 else total
    calibrate_end = max(train_end + 1, int(total * (train_ratio + calibrate_ratio))) if total >= 5 else total

    if total < 5:
        return TemporalSplit(train=ordered, calibrate=[], test=[])

    return TemporalSplit(
        train=ordered[:train_end],
        calibrate=ordered[train_end:calibrate_end],
        test=ordered[calibrate_end:],
    )
