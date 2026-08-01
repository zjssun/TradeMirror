from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class InsightsQuery(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=64)
    direction: Literal["BUY", "SELL"] | None = None
    from_time: datetime | None = Field(default=None, alias="from")
    to_time: datetime | None = Field(default=None, alias="to")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_range(self) -> "InsightsQuery":
        if self.from_time and self.to_time and self.from_time > self.to_time:
            raise ValueError("开始时间不能晚于结束时间。")
        return self


class InsightsResponse(BaseModel):
    filters: dict[str, object]
    statistics: dict[str, object]
    profile: dict[str, object]
    prompt: str
    completed_context_count: int
    insufficient_data_context_count: int
    equity_curve: list[dict[str, object]]
