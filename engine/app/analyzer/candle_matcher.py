from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, timedelta

from app.schemas.market import CandleTimeframe, MarketCandle


_TIMEFRAME_DURATIONS = {
    CandleTimeframe.M1: timedelta(minutes=1),
    CandleTimeframe.M5: timedelta(minutes=5),
    CandleTimeframe.M15: timedelta(minutes=15),
    CandleTimeframe.M30: timedelta(minutes=30),
    CandleTimeframe.H1: timedelta(hours=1),
    CandleTimeframe.H4: timedelta(hours=4),
    CandleTimeframe.D1: timedelta(days=1),
}


@dataclass(frozen=True)
class CandleWindows:
    pre: list[MarketCandle]
    holding: list[MarketCandle]
    post: list[MarketCandle]


def timeframe_duration(timeframe: CandleTimeframe) -> timedelta:
    return _TIMEFRAME_DURATIONS[timeframe]


def _utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def split_candles(
    candles: list[MarketCandle],
    timeframe: CandleTimeframe,
    open_time,
    close_time,
) -> CandleWindows:
    open_time, close_time = _utc(open_time), _utc(close_time)
    duration = timeframe_duration(timeframe)
    pre = [candle for candle in candles if candle.time + duration <= open_time][-80:]
    holding = [
        candle
        for candle in candles
        if candle.time < close_time and candle.time + duration > open_time
    ]
    post = [candle for candle in candles if candle.time >= close_time][:20]
    return CandleWindows(pre=pre, holding=holding, post=post)
