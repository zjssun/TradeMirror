from app.schemas.insights import InsightsQuery


def test_insights_reject_invalid_time_range() -> None:
    from datetime import UTC, datetime
    import pytest

    with pytest.raises(ValueError, match="开始时间"):
        InsightsQuery(**{"from": datetime(2025, 1, 2, tzinfo=UTC), "to": datetime(2025, 1, 1, tzinfo=UTC)})
