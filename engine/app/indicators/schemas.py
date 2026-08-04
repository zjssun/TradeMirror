from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.indicators.registry import resolve_parameters
from app.schemas.market import CandleTimeframe, MarketCandle

IndicatorName = Literal["SMA", "EMA", "BOLLINGER_BANDS", "RSI", "MACD", "ATR"]


class IndicatorRequest(BaseModel):
    name: IndicatorName
    parameters: dict[str, float | int] = Field(default_factory=dict)


class IndicatorCalculationRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    timeframe: CandleTimeframe
    indicators: list[IndicatorRequest] = Field(min_length=1, max_length=12)
    candles: list[MarketCandle] = Field(min_length=1, max_length=5_000)

    @model_validator(mode="after")
    def validate_indicator_requests(self) -> "IndicatorCalculationRequest":
        normalized = []
        for item in self.indicators:
            parameters = resolve_parameters(item.name, item.parameters)
            normalized.append((item.name, tuple(sorted(parameters.items()))))
        if len(set(normalized)) != len(normalized):
            raise ValueError("指标不能重复。")
        return self


class IndicatorPoint(BaseModel):
    time: datetime
    value: float
    source_index: int


class IndicatorSeries(BaseModel):
    id: str
    name: IndicatorName
    display_name: str
    pane: Literal["main", "separate"]
    parameters: dict[str, float | int]
    series: list[IndicatorPoint] | dict[str, list[IndicatorPoint]]


class IndicatorCalculationResponse(BaseModel):
    symbol: str
    timeframe: CandleTimeframe
    candle_count: int
    provider: str
    provider_version: str
    indicators: list[IndicatorSeries]
