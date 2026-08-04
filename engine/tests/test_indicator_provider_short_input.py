from datetime import UTC, datetime

from app.indicators.providers.ta_provider import TaIndicatorProvider
from app.schemas.market import MarketCandle


def candle() -> MarketCandle:
    return MarketCandle(
        time=datetime(2025, 1, 1, tzinfo=UTC),
        open=100, high=101, low=99, close=100,
        tick_volume=1, spread=0, real_volume=0,
    )


def test_provider_returns_empty_warmup_values_for_short_atr_input() -> None:
    result = TaIndicatorProvider().calculate("ATR", [candle()] * 13, {"period": 14})

    assert result == {"value": [None] * 13}


def test_provider_returns_empty_warmup_values_for_short_macd_input() -> None:
    result = TaIndicatorProvider().calculate("MACD", [candle()] * 33, {"fast": 12, "slow": 26, "signal": 9})

    assert result == {"macd": [None] * 33, "signal": [None] * 33, "histogram": [None] * 33}
