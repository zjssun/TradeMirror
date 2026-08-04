from datetime import UTC, datetime, timedelta

import pytest

from app.indicators.calculator import IndicatorCalculator
from app.indicators.providers.ta_provider import TaIndicatorProvider
from app.indicators.schemas import IndicatorCalculationRequest, IndicatorRequest
from app.schemas.market import CandleTimeframe, MarketCandle


def candles(count: int = 80) -> list[MarketCandle]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        MarketCandle(
            time=start + timedelta(minutes=15 * index),
            open=100 + index * 0.1,
            high=101 + index * 0.1,
            low=99 + index * 0.1,
            close=100.5 + index * 0.1,
            tick_volume=100,
            spread=0,
            real_volume=0,
        )
        for index in range(count)
    ]


def test_calculator_returns_json_safe_aligned_series() -> None:
    calculator = IndicatorCalculator(TaIndicatorProvider())
    result = calculator.calculate(
        IndicatorCalculationRequest(
            symbol="XAUUSD",
            timeframe=CandleTimeframe.M15,
            candles=candles(),
            indicators=[
                IndicatorRequest(name="SMA", parameters={"period": 20}),
                IndicatorRequest(name="EMA", parameters={"period": 20}),
                IndicatorRequest(name="BOLLINGER_BANDS", parameters={"period": 20, "std_dev": 2}),
                IndicatorRequest(name="RSI", parameters={"period": 14}),
                IndicatorRequest(name="MACD", parameters={"fast": 12, "slow": 26, "signal": 9}),
                IndicatorRequest(name="ATR", parameters={"period": 14}),
            ],
        )
    )

    assert result.provider == "ta"
    assert len(result.indicators) == 6
    for indicator in result.indicators:
        fields = {"value": indicator.series} if isinstance(indicator.series, list) else indicator.series
        for points in fields.values():
            assert points
            assert all(point.source_index >= 0 for point in points)
            assert all(point.value == point.value for point in points)


def test_calculator_sorts_and_deduplicates_candles() -> None:
    source = candles(30)
    result = IndicatorCalculator(TaIndicatorProvider()).calculate(
        IndicatorCalculationRequest(
            symbol="EURUSD",
            timeframe=CandleTimeframe.M15,
            candles=[source[2], source[0], source[1], source[1]],
            indicators=[IndicatorRequest(name="SMA", parameters={"period": 2})],
        )
    )

    assert result.candle_count == 3
    assert result.indicators[0].series[0].source_index == 1




def test_calculator_rejects_invalid_ohlc() -> None:
    invalid = candles(2)
    invalid[0] = invalid[0].model_copy(update={"high": 99})
    with pytest.raises(ValueError, match="OHLC"):
        IndicatorCalculator(TaIndicatorProvider()).calculate(
            IndicatorCalculationRequest(
                symbol="EURUSD", timeframe=CandleTimeframe.M15, candles=invalid,
                indicators=[IndicatorRequest(name="SMA", parameters={"period": 2})],
            )
        )


def test_snapshot_keeps_each_ema_parameter_set() -> None:
    from app.indicators.schemas import IndicatorRequest

    snapshot = IndicatorCalculator(TaIndicatorProvider()).snapshot(
        candles(),
        [
            IndicatorRequest(name="EMA", parameters={"period": 20}),
            IndicatorRequest(name="EMA", parameters={"period": 50}),
        ],
    )

    assert snapshot["parameters"] == {"ema-20": {"period": 20}, "ema-50": {"period": 50}}
    assert set(snapshot["values"]) == {"ema-20", "ema-50"}
