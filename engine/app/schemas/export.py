from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TmfExportRequest(BaseModel):
    trade_ids: list[int] | None = None
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    direction: Literal["BUY", "SELL"] | None = None
    source: Literal["MT5", "CSV"] | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    include_charts: bool = True
    redact_source_identity: bool = True

    @model_validator(mode="after")
    def validate_scope(self) -> "TmfExportRequest":
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
