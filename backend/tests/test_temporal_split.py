from datetime import datetime, timezone

import pytest

from app.pipeline.temporal_split import expanding_walk_forward, split_by_time


def test_split_by_time_orders_and_partitions() -> None:
    rows = [
        {"id": 1, "resolved_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        {"id": 2, "resolved_at": datetime(2026, 2, 1, tzinfo=timezone.utc)},
        {"id": 3, "resolved_at": datetime(2026, 3, 1, tzinfo=timezone.utc)},
        {"id": 4, "resolved_at": datetime(2026, 4, 1, tzinfo=timezone.utc)},
        {"id": 5, "resolved_at": datetime(2026, 5, 1, tzinfo=timezone.utc)},
        {"id": 6, "resolved_at": datetime(2026, 6, 1, tzinfo=timezone.utc)},
        {"id": 7, "resolved_at": datetime(2026, 7, 1, tzinfo=timezone.utc)},
        {"id": 8, "resolved_at": datetime(2026, 8, 1, tzinfo=timezone.utc)},
        {"id": 9, "resolved_at": datetime(2026, 9, 1, tzinfo=timezone.utc)},
        {"id": 10, "resolved_at": datetime(2026, 10, 1, tzinfo=timezone.utc)},
    ]
    split = split_by_time(rows, sort_key=lambda row: row["resolved_at"])
    assert split.train[0]["id"] == 1
    assert split.test[-1]["id"] == 10
    assert len(split.train) + len(split.calibrate) + len(split.test) == 10
    assert all(
        split.train[i]["resolved_at"] <= split.train[i + 1]["resolved_at"]
        for i in range(len(split.train) - 1)
    )


def test_split_by_time_returns_all_train_when_too_few_rows() -> None:
    rows = [{"id": 1, "resolved_at": datetime(2026, 1, 1, tzinfo=timezone.utc)}]
    split = split_by_time(rows, sort_key=lambda row: row["resolved_at"])
    assert split.train == rows
    assert split.calibrate == []
    assert split.test == []


def test_expanding_walk_forward_never_leaks_future_rows() -> None:
    rows = list(range(12))
    folds = expanding_walk_forward(
        rows,
        sort_key=lambda value: value,
        min_train_size=4,
        calibrate_size=2,
        test_size=2,
    )

    assert len(folds) == 3
    assert folds[0].train == [0, 1, 2, 3]
    assert folds[0].calibrate == [4, 5]
    assert folds[0].test == [6, 7]
    assert folds[1].train == [0, 1, 2, 3, 4, 5]
    for fold in folds:
        assert max(fold.train) < min(fold.calibrate)
        assert max(fold.calibrate) < min(fold.test)


def test_expanding_walk_forward_validates_window_sizes() -> None:
    with pytest.raises(ValueError, match="positive"):
        expanding_walk_forward(
            [1, 2, 3],
            sort_key=lambda value: value,
            min_train_size=0,
            calibrate_size=1,
            test_size=1,
        )
