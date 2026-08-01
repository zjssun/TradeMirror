from __future__ import annotations

import math

from app.schemas.market import MarketCandle


def indicators(candles: list[MarketCandle]) -> dict[str, float | None]:
    if len(candles) < 50:
        return {"rsi": None, "atr": None, "ema20": None, "ema50": None}
    closes = [c.close for c in candles]
    ema = lambda period: _ema(closes, period)
    return {"rsi": _rsi(closes, 14), "atr": _atr(candles, 14), "ema20": ema(20), "ema50": ema(50)}


def _ema(values, period):
    value = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    for price in values[period:]: value = (price - value) * multiplier + value
    return value


def _rsi(closes, period):
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]
    avg_gain, avg_loss = sum(gains[:period]) / period, sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain, avg_loss = (avg_gain * (period - 1) + gain) / period, (avg_loss * (period - 1) + loss) / period
    return 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)


def _atr(candles, period):
    ranges = [max(c.high - c.low, abs(c.high - previous.close), abs(c.low - previous.close)) for previous, c in zip(candles, candles[1:])]
    return sum(ranges[-period:]) / period
