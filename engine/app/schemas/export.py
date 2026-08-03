from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.market import CandleTimeframe, MarketCandle


class TmfReplaySnapshot(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    timeframe: CandleTimeframe
    from_time: datetime = Field(alias="from")
    to_time: datetime = Field(alias="to")
    candle_from: datetime
    candle_to: datetime
    candles: list[MarketCandle] = Field(min_length=1)
    pre_roll_candles: int = Field(ge=0, le=500)
    post_roll_candles: int = Field(ge=0, le=500)
    available_pre_roll_candles: int = Field(ge=0, le=500)
    initial_cursor: int = Field(ge=0)
    cursor: int = Field(ge=0)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_snapshot(self) -> "TmfReplaySnapshot":
        if self.from_time.tzinfo is None or self.to_time.tzinfo is None:
            raise ValueError("回放时间范围必须包含 UTC 时区信息。")
        if self.from_time > self.to_time or self.candle_from > self.candle_to:
            raise ValueError("回放时间范围无效。")
        if self.initial_cursor > self.cursor or self.cursor >= len(self.candles):
            raise ValueError("回放进度超出 K 线范围。")
        times = [candle.time for candle in self.candles]
        if any(time.tzinfo is None for time in times) or any(left >= right for left, right in zip(times, times[1:])):
            raise ValueError("回放 K 线必须按 UTC 时间严格递增。")
        return self


class TmfExportRequest(BaseModel):
    trade_ids: list[int] | None = None
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    direction: Literal["BUY", "SELL"] | None = None
    source: Literal["MT5", "CSV"] | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    include_charts: bool = True
    redact_source_identity: bool = True
    replay: TmfReplaySnapshot | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "TmfExportRequest":
        if self.replay and self.trade_ids is None:
            raise ValueError("回放导出必须指定交易 ID。")
        if self.trade_ids is not None:
            if not self.trade_ids:
                raise ValueError("至少选择一笔交易。")
            if len(set(self.trade_ids)) != len(self.trade_ids):
                raise ValueError("交易不能重复。")
            if self.symbol or self.direction or self.source or self.from_time or self.to_time:
                raise ValueError("不能同时指定交易 ID 和筛选条件。")
        elif not any((self.symbol, self.direction, self.source, self.from_time, self.to_time)):
            raise ValueError("请选择交易或至少提供一个筛选条件。")
        if self.from_time and self.to_time and self.from_time > self.to_time:
            raise ValueError("开始时间不能晚于结束时间。")
        return self


class TmfExportResponse(BaseModel):
    export_id: str
    filename: str
    trade_count: int
    include_charts: bool
    redact_source_identity: bool
    validation_passed: bool
    statistics: dict[str, object]
