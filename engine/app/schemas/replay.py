from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.market import CandleTimeframe, MarketCandle


class ReplaySymbolOption(BaseModel):
    symbol: str
    available_from: datetime
    available_to: datetime
    trade_count: int


class ReplayTradeEvent(BaseModel):
    trade_id: int
    source: str
    ticket: str
    symbol: str
    direction: str
    open_time: datetime
    close_time: datetime
    open_price: float
    close_price: float
    volume: float
    profit: float
    commission: float
    swap: float
    net_profit: float
    stop_loss: float | None
    take_profit: float | None
    close_reason: str | None


class ReplayQuery(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    from_time: datetime = Field(alias="from")
    to_time: datetime = Field(alias="to")
    pre_roll_candles: int = Field(default=20, ge=0, le=500)
    post_roll_candles: int = Field(default=20, ge=0, le=500)
    timeframe: CandleTimeframe | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_range(self) -> "ReplayQuery":
        if self.from_time.tzinfo is None or self.to_time.tzinfo is None:
            raise ValueError("时间范围必须包含 UTC 时区信息")
        if self.from_time > self.to_time:
            raise ValueError("开始时间不能晚于结束时间")
        if self.timeframe not in {None, CandleTimeframe.M1, CandleTimeframe.M5, CandleTimeframe.M15, CandleTimeframe.H1, CandleTimeframe.H4}:
            raise ValueError("回放周期仅支持 M1、M5、M15、H1 或 H4。")
        return self


class ReplayResponse(BaseModel):
    symbol: str
    timeframe: CandleTimeframe
    from_time: datetime = Field(alias="from")
    to_time: datetime = Field(alias="to")
    candle_from: datetime
    candle_to: datetime
    candles: list[MarketCandle]
    events: list[ReplayTradeEvent]
    cached_count: int
    fetched_count: int
    pre_roll_candles: int
    post_roll_candles: int
    selected_trade_count: int
    selected_net_profit: float
    initial_cursor: int
    available_pre_roll_candles: int

    model_config = {"populate_by_name": True}
