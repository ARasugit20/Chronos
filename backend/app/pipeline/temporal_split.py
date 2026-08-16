# WHY: Time-ordered train/calibrate/test splits to prevent leakage in ML retraining.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class TemporalSplit(Generic[T]):
    train: list[T]
    calibrate: list[T]
    test: list[T]


@dataclass(frozen=True)
class WalkForwardFold(Generic[T]):
    fold: int
    train: list[T]
    calibrate: list[T]
    test: list[T]


def split_by_time(
    rows: list[T],
    *,
    train_ratio: float = 0.70,
    calibrate_ratio: float = 0.15,
    sort_key: Callable[[T], Any],
) -> TemporalSplit[T]:
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


def expanding_walk_forward(
    rows: list[T],
    *,
    sort_key: Callable[[T], Any],
    min_train_size: int,
    calibrate_size: int,
    test_size: int,
) -> list[WalkForwardFold[T]]:
    """Build non-overlapping OOS windows with an expanding training history."""
    if min_train_size < 1 or calibrate_size < 1 or test_size < 1:
        raise ValueError("walk-forward window sizes must be positive")

    ordered = sorted(rows, key=sort_key)
    folds: list[WalkForwardFold[T]] = []
    train_end = min_train_size
    fold_number = 1
    while train_end + calibrate_size + test_size <= len(ordered):
        calibrate_end = train_end + calibrate_size
        test_end = calibrate_end + test_size
        folds.append(
            WalkForwardFold(
                fold=fold_number,
                train=ordered[:train_end],
                calibrate=ordered[train_end:calibrate_end],
                test=ordered[calibrate_end:test_end],
            )
        )
        train_end += test_size
        fold_number += 1
    return folds
