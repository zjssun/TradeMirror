from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DataSourceStatusResponse(BaseModel):
    source: Literal["MT5", "CSV"]
    available: bool
    recommended: bool
    message: str
    remediation: str | None = None


class DataSourceSyncResponse(BaseModel):
    source: Literal["MT5", "CSV"]
    account_id: str | None = None
    symbol: str | None = None
    from_time: datetime
    to_time: datetime
    status: str
    trade_count: int
    diagnostic: str | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class Mt5HistorySyncRequest(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    sync_all: bool = False
    from_time: datetime
    to_time: datetime

    @model_validator(mode="after")
    def validate_range(self) -> "Mt5HistorySyncRequest":
        if self.to_time <= self.from_time:
            raise ValueError("结束时间必须晚于开始时间。")
        return self


class Mt5HistorySyncResponse(BaseModel):
    source: Literal["MT5"] = "MT5"
    account_id: str
    imported_count: int
    updated_count: int
    skipped_count: int
    from_time: datetime
    to_time: datetime
