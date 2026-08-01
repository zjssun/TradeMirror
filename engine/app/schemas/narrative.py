from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TradingNarrativeRequest(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    direction: Literal["BUY", "SELL"] | None = None
    source: Literal["MT5", "CSV"] | None = None
    from_time: datetime
    to_time: datetime

    @model_validator(mode="after")
    def validate_range(self) -> "TradingNarrativeRequest":
        if self.from_time.tzinfo is None or self.to_time.tzinfo is None:
            raise ValueError("时间范围必须包含 UTC 时区信息。")
        if self.from_time >= self.to_time:
            raise ValueError("开始时间必须早于结束时间。")
        return self


class TradingNarrativeResponse(BaseModel):
    filters: dict[str, Any]
    trade_count: int
    narrative: str
    timeline: list[dict[str, Any]]
    markets: list[dict[str, Any]]
    diagnostics: list[str]
