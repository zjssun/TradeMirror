from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class DataSource(ABC):
    name: str

    @abstractmethod
    def status(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_symbols(self, query: str | None = None, visible_only: bool = True, limit: int = 200) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, from_time: datetime, to_time: datetime) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_trades(self, symbol: str | None = None, from_time: datetime | None = None, to_time: datetime | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError
