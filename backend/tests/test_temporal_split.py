from datetime import datetime, timezone

from app.pipeline.temporal_split import split_by_time


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
