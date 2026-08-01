from __future__ import annotations

from datetime import datetime
from typing import Any

from app.datasource.base import DataSource
from app.datasource.models import DataSourceStatus
from app.mt5.client import Mt5Client, Mt5ClientError
from app.mt5.connection_service import Mt5ConnectionService
from app.mt5.market_data_service import MarketDataService
from app.mt5.symbol_service import SymbolService
from app.schemas.market import CandleQuery, CandleTimeframe


class Mt5DataSource(DataSource):
    name = "MT5"

    def __init__(self, client: Mt5Client, database) -> None:
        self._client = client
        self._database = database

    def status(self) -> DataSourceStatus:
        connection = Mt5ConnectionService(self._client).status()
        if connection.state == "connected":
            return DataSourceStatus(
                source="MT5",
                available=True,
                recommended=True,
                message="MetaTrader 5 已连接，可作为默认交易数据源。",
            )
        diagnostic = connection.diagnostic
        return DataSourceStatus(
            source="MT5",
            available=False,
            recommended=True,
            message=diagnostic.message if diagnostic else "MetaTrader 5 当前不可用。",
            remediation=diagnostic.remediation if diagnostic else "请连接 MT5，或使用 CSV 兼容导入。",
        )

    def get_symbols(self, query: str | None = None, visible_only: bool = True, limit: int = 200) -> Any:
        return SymbolService(self._client).list_symbols(query, visible_only, limit)

    def get_candles(self, symbol: str, timeframe: str, from_time: datetime, to_time: datetime) -> Any:
        return MarketDataService(self._client, self._database).get_candles(
            CandleQuery(
                symbol=symbol,
                timeframe=CandleTimeframe(timeframe),
                **{"from": from_time, "to": to_time},
            )
        )

    def get_trades(self, symbol: str | None = None, from_time: datetime | None = None, to_time: datetime | None = None) -> list[dict[str, Any]]:
        raise Mt5ClientError(
            "mt5_history_sync_not_available",
            "MT5 历史交易同步尚未启用。",
            "请完成历史同步配置后重试，或使用 CSV 兼容导入。",
        )
