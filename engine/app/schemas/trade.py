from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class TradeResponse(BaseModel):
    id: int
    import_batch_id: int | None
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

    model_config = {"from_attributes": True}


class TradeDeleteRequest(BaseModel):
    trade_ids: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_trade_ids(self) -> "TradeDeleteRequest":
        if len(set(self.trade_ids)) != len(self.trade_ids):
            raise ValueError("交易不能重复。")
        return self


class TradeDeleteResponse(BaseModel):
    deleted_count: int


class TradeDateRangeResponse(BaseModel):
    from_time: datetime | None = None
    to_time: datetime | None = None


class TradeListResponse(BaseModel):
    items: list[TradeResponse]
    total: int
    page: int
    page_size: int
