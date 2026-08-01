from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TradeEvent(BaseModel):
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
    result: dict[str, float]
    context_status: str
    context: dict[str, Any] | None = None
