from __future__ import annotations

from datetime import datetime
from typing import Any

from app.database.repositories.trade_repository import TradeRepository
from app.datasource.base import DataSource
from app.datasource.models import DataSourceStatus
from app.importer.import_service import ImportService


class CsvDataSource(DataSource):
    name = "CSV"

    def __init__(self, database, importer: ImportService) -> None:
        self._database = database
        self._importer = importer

    def status(self) -> DataSourceStatus:
        return DataSourceStatus(
            source="CSV",
            available=True,
            recommended=False,
            message="CSV 兼容导入可用。",
        )

    def get_symbols(self, query: str | None = None, visible_only: bool = True, limit: int = 200) -> list[Any]:
        return []

    def get_candles(self, symbol: str, timeframe: str, from_time: datetime, to_time: datetime) -> list[Any]:
        return []

    def get_trades(self, symbol: str | None = None, from_time: datetime | None = None, to_time: datetime | None = None) -> list[dict[str, Any]]:
        trades = TradeRepository(self._database).get_for_export(symbol=symbol, from_time=from_time, to_time=to_time)
        return [
            {
                "id": trade.id,
                "ticket": trade.ticket,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "open_time": trade.open_time,
                "close_time": trade.close_time,
                "open_price": trade.open_price,
                "close_price": trade.close_price,
                "volume": trade.volume,
                "profit": trade.profit,
                "commission": trade.commission,
                "swap": trade.swap,
                "source": trade.source,
            }
            for trade in trades
            if trade.source == self.name
        ]
