from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class CandleTimeframe(StrEnum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


MAX_CANDLES_PER_REQUEST = 5_000
CANDLES_PER_DAY = {
    CandleTimeframe.M1: 1_440,
    CandleTimeframe.M5: 288,
    CandleTimeframe.M15: 96,
    CandleTimeframe.M30: 48,
    CandleTimeframe.H1: 24,
    CandleTimeframe.H4: 6,
    CandleTimeframe.D1: 1,
}


class MarketCandle(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread: float
    real_volume: float


class CandleResponse(BaseModel):
    symbol: str
    timeframe: CandleTimeframe
    from_time: datetime = Field(alias="from")
    to_time: datetime = Field(alias="to")
    candles: list[MarketCandle]
    cached_count: int
    fetched_count: int

    model_config = {"populate_by_name": True}


class CandleQuery(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    timeframe: CandleTimeframe
    from_time: datetime = Field(alias="from")
    to_time: datetime = Field(alias="to")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_range(self) -> "CandleQuery":
        if self.from_time.tzinfo is None or self.to_time.tzinfo is None:
            raise ValueError("时间范围必须包含 UTC 时区信息")
        if self.from_time >= self.to_time:
            raise ValueError("开始时间必须早于结束时间")
        range_days = (self.to_time - self.from_time).total_seconds() / 86_400
        if range_days > 366:
            raise ValueError("单次最多读取 366 天历史K线")
        estimated_candles = range_days * CANDLES_PER_DAY[self.timeframe]
        if estimated_candles > MAX_CANDLES_PER_REQUEST:
            raise ValueError(f"所选范围预计超过 {MAX_CANDLES_PER_REQUEST} 根K线，请缩短时间范围或选择更高周期。")
        return self
