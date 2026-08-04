from __future__ import annotations

from importlib.metadata import version
from math import isfinite

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands

from app.indicators.base import IndicatorProvider
from app.schemas.market import MarketCandle


class TaIndicatorProvider(IndicatorProvider):
    name = "ta"
    version = version("ta")

    def calculate(
        self,
        name: str,
        candles: list[MarketCandle],
        parameters: dict[str, float | int],
    ) -> dict[str, list[float | None]]:
        frame = pd.DataFrame(
            {
                "high": [candle.high for candle in candles],
                "low": [candle.low for candle in candles],
                "close": [candle.close for candle in candles],
            }
        )
        close = frame["close"]
        required = self._required_candles(name, parameters)
        if len(candles) < required:
            return {field: [None] * len(candles) for field in self._fields(name)}
        if name == "SMA":
            return {"value": self._values(SMAIndicator(close, window=int(parameters["period"])).sma_indicator(), int(parameters["period"]) - 1)}
        if name == "EMA":
            return {"value": self._values(EMAIndicator(close, window=int(parameters["period"])).ema_indicator(), int(parameters["period"]) - 1)}
        if name == "BOLLINGER_BANDS":
            bands = BollingerBands(close, window=int(parameters["period"]), window_dev=float(parameters["std_dev"]))
            return {
                "upper": self._values(bands.bollinger_hband(), int(parameters["period"]) - 1),
                "middle": self._values(bands.bollinger_mavg(), int(parameters["period"]) - 1),
                "lower": self._values(bands.bollinger_lband(), int(parameters["period"]) - 1),
            }
        if name == "RSI":
            return {"value": self._values(RSIIndicator(close, window=int(parameters["period"])).rsi(), int(parameters["period"]))}
        if name == "MACD":
            macd = MACD(
                close,
                window_fast=int(parameters["fast"]),
                window_slow=int(parameters["slow"]),
                window_sign=int(parameters["signal"]),
            )
            return {
                "macd": self._values(macd.macd(), int(parameters["slow"]) - 1),
                "signal": self._values(macd.macd_signal(), int(parameters["slow"]) + int(parameters["signal"]) - 2),
                "histogram": self._values(macd.macd_diff(), int(parameters["slow"]) + int(parameters["signal"]) - 2),
            }
        if name == "ATR":
            atr = AverageTrueRange(frame["high"], frame["low"], close, window=int(parameters["period"])).average_true_range()
            return {"value": self._values(atr, int(parameters["period"]) - 1)}
        raise ValueError(f"不支持的指标：{name}。")

    @staticmethod
    def _fields(name: str) -> tuple[str, ...]:
        return {
            "SMA": ("value",),
            "EMA": ("value",),
            "BOLLINGER_BANDS": ("upper", "middle", "lower"),
            "RSI": ("value",),
            "MACD": ("macd", "signal", "histogram"),
            "ATR": ("value",),
        }[name]

    @staticmethod
    def _required_candles(name: str, parameters: dict[str, float | int]) -> int:
        if name == "MACD":
            return int(parameters["slow"]) + int(parameters["signal"]) - 1
        return int(parameters["period"])

    @staticmethod
    def _values(series: pd.Series, warmup: int = 0) -> list[float | None]:
        return [
            float(value) if index >= warmup and pd.notna(value) and isfinite(float(value)) else None
            for index, value in enumerate(series.tolist())
        ]
