from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.market import CandleTimeframe, MarketCandle


class BatchAnalyzeRequest(BaseModel):
    trade_ids: list[int] | None = None
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    direction: Literal["BUY", "SELL"] | None = None
    all: bool = False

    @model_validator(mode="after")
    def validate_target(self) -> "BatchAnalyzeRequest":
        if self.all:
            if self.trade_ids is not None or self.symbol or self.direction:
                raise ValueError("复盘全部不能同时指定交易或筛选条件。")
            return self
        if self.trade_ids is not None:
            if not self.trade_ids:
                raise ValueError("至少选择一笔交易。")
            if len(set(self.trade_ids)) != len(self.trade_ids):
                raise ValueError("交易不能重复。")
            if self.symbol or self.direction:
                raise ValueError("不能同时指定交易 ID 和筛选条件。")
        elif not self.symbol and not self.direction:
            raise ValueError("请选择交易或至少提供一个筛选条件。")
        return self


class BatchAnalyzeItem(BaseModel):
    trade_id: int
    status: Literal["completed", "insufficient_data", "failed"]
    error_message: str | None = None


class BatchAnalyzeResponse(BaseModel):
    requested_count: int
    completed_count: int
    insufficient_data_count: int
    failed_count: int
    items: list[BatchAnalyzeItem]


class TradeContextResponse(BaseModel):
    trade_id: int
    status: Literal["completed", "insufficient_data", "not_analyzed"]
    timeframe: CandleTimeframe | None = None
    data_quality: dict[str, object] = {}
    market_context: dict[str, object] = {}
    execution: dict[str, object] = {}
    candles: list[MarketCandle] = []
    error_message: str | None = None
    analyzed_at: datetime | None = None
