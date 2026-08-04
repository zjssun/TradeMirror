from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite

from app.indicators.base import IndicatorProvider
from app.indicators.registry import DEFINITIONS, resolve_parameters
from app.indicators.schemas import (
    IndicatorCalculationRequest,
    IndicatorCalculationResponse,
    IndicatorPoint,
    IndicatorRequest,
    IndicatorSeries,
)
from app.schemas.market import MarketCandle


class IndicatorCalculator:
    """Normalizes OHLCV input and converts provider output into API series."""

    def __init__(self, provider: IndicatorProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def provider_version(self) -> str:
        return self._provider.version

    def calculate(self, request: IndicatorCalculationRequest) -> IndicatorCalculationResponse:
        candles = self.normalize_candles(request.candles)
        normalized_requests = self._normalized_requests(request.indicators)
        results = [self._series(item, candles) for item in normalized_requests]
        return IndicatorCalculationResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            candle_count=len(candles),
            provider=self.provider_name,
            provider_version=self.provider_version,
            indicators=results,
        )

    def snapshot(self, candles: list[MarketCandle], indicators: list[IndicatorRequest]) -> dict[str, object]:
        normalized = self.normalize_candles(candles)
        values: dict[str, object] = {}
        parameters: dict[str, dict[str, float | int]] = {}
        for request in self._normalized_requests(indicators):
            resolved = request.parameters
            calculated = self._provider.calculate(request.name, normalized, resolved)
            instance_id = self._series_id(request.name, resolved)
            parameters[instance_id] = resolved
            if request.name == "MACD":
                values["macd"] = {
                    field: self._last_valid(series)
                    for field, series in calculated.items()
                }
            elif request.name == "BOLLINGER_BANDS":
                values["bollinger_bands"] = {
                    field: self._last_valid(series)
                    for field, series in calculated.items()
                }
            else:
                key = instance_id
                values[key] = self._last_valid(calculated["value"])
        as_of = normalized[-1].time.astimezone(UTC).isoformat() if normalized else None
        return {
            "as_of": as_of,
            "source_candle_count": len(normalized),
            "parameters": parameters,
            "values": values,
            "provider": self.provider_name,
            "provider_version": self.provider_version,
        }

    def _normalized_requests(self, requests: list[IndicatorRequest]) -> list[IndicatorRequest]:
        normalized: list[IndicatorRequest] = []
        seen = set()
        for request in requests:
            parameters = resolve_parameters(request.name, request.parameters)
            key = (request.name, tuple(sorted(parameters.items())))
            if key in seen:
                raise ValueError("指标不能重复。")
            seen.add(key)
            normalized.append(IndicatorRequest(name=request.name, parameters=parameters))
        return normalized

    @staticmethod
    def normalize_candles(candles: list[MarketCandle]) -> list[MarketCandle]:
        by_time: dict[datetime, MarketCandle] = {}
        for candle in candles:
            if candle.time.tzinfo is None:
                raise ValueError("指标K线时间必须包含时区信息。")
            time = candle.time.astimezone(UTC)
            values = (candle.open, candle.high, candle.low, candle.close, candle.tick_volume, candle.spread, candle.real_volume)
            if not all(isfinite(value) for value in values):
                raise ValueError("指标K线不能包含非有限数值。")
            if candle.tick_volume < 0 or candle.real_volume < 0 or candle.spread < 0:
                raise ValueError("指标K线成交量和点差不能为负数。")
            if candle.high < max(candle.open, candle.close, candle.low) or candle.low > min(candle.open, candle.close, candle.high):
                raise ValueError("指标K线OHLC数据不合法。")
            by_time[time] = candle.model_copy(update={"time": time})
        return [by_time[time] for time in sorted(by_time)]

    def _series(self, request: IndicatorRequest, candles: list[MarketCandle]) -> IndicatorSeries:
        parameters = resolve_parameters(request.name, request.parameters)
        definition = DEFINITIONS[request.name]
        raw = self._provider.calculate(request.name, candles, parameters)
        series = {
            field: self._points(candles, values)
            for field, values in raw.items()
        }
        output: list[IndicatorPoint] | dict[str, list[IndicatorPoint]]
        output = series["value"] if definition.series_fields == ("value",) else series
        return IndicatorSeries(
            id=self._series_id(request.name, parameters),
            name=request.name,
            display_name=self._display_name(request.name, parameters),
            pane=definition.pane,
            parameters=parameters,
            series=output,
        )

    @staticmethod
    def _points(candles: list[MarketCandle], values: list[float | None]) -> list[IndicatorPoint]:
        return [
            IndicatorPoint(time=candle.time.astimezone(UTC), value=float(value), source_index=index)
            for index, (candle, value) in enumerate(zip(candles, values, strict=True))
            if value is not None and isfinite(value)
        ]

    @staticmethod
    def _last_valid(values: list[float | None]) -> float | None:
        for value in reversed(values):
            if value is not None and isfinite(value):
                return float(value)
        return None

    @staticmethod
    def _series_id(name: str, parameters: dict[str, float | int]) -> str:
        values = "-".join(str(value).rstrip("0").rstrip(".") if isinstance(value, float) else str(value) for value in parameters.values())
        return f"{name.lower().replace('_', '-')}-{values}"

    @staticmethod
    def _display_name(name: str, parameters: dict[str, float | int]) -> str:
        if name == "BOLLINGER_BANDS":
            return f"Bollinger Bands {parameters['period']}, {parameters['std_dev']}"
        if name == "MACD":
            return f"MACD {parameters['fast']}, {parameters['slow']}, {parameters['signal']}"
        return f"{name} {parameters['period']}"
