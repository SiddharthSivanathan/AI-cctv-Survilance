"""Unit tests for the metrics aggregator."""

from src.metrics.aggregator import MetricsAggregator, minute_of


def test_minute_of() -> None:
    assert minute_of(125.0) == 120
    assert minute_of(60.0) == 60


def test_aggregator_buckets_and_flush() -> None:
    agg = MetricsAggregator()
    # Two samples in minute 0
    agg.record("cam1", 3, 1, {1, 2}, now=10.0)
    agg.record("cam1", 5, 2, {2, 3}, now=40.0)
    # Nothing flushes while still in minute 0
    assert agg.flush_due(now=50.0) == []

    # Advance to minute 1 -> minute 0 bucket flushes
    due = agg.flush_due(now=65.0)
    assert len(due) == 1
    m = due[0]
    assert m["camera_id"] == "cam1"
    assert m["bucket"] == 0.0
    assert m["occupancy_avg"] == 4.0  # (3+5)/2
    assert m["occupancy_peak"] == 5
    assert m["footfall"] == 3  # unique tracks {1,2,3}
    assert m["queue_peak"] == 2


def test_flush_only_completed_buckets() -> None:
    agg = MetricsAggregator()
    agg.record("cam1", 2, 0, set(), now=125.0)  # minute 120
    # current minute is 120 -> nothing due
    assert agg.flush_due(now=150.0) == []
