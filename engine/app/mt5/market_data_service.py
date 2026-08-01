from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.engine import Engine

from app.database.repositories.candle_repository import CandleRepository
from app.mt5.client import Mt5Client
from app.schemas.market import CandleQuery, CandleResponse, MarketCandle
from app.schemas.mt5 import SymbolResponse


class MarketDataService:
    def __init__(self, client: Mt5Client, database: Engine) -> None:
        self._client = client
        self._repository = CandleRepository(database)

    def get_candles(self, query: CandleQuery) -> CandleResponse:
        from_time = query.from_time.astimezone(UTC)
        to_time = query.to_time.astimezone(UTC)
        cached = self._repository.get_candles(query.symbol, query.timeframe.value, from_time, to_time)
        if cached and cached[0].time <= from_time and cached[-1].time >= to_time:
            return CandleResponse(
                symbol=query.symbol,
                timeframe=query.timeframe,
                **{"from": from_time, "to": to_time},
                candles=cached,
                cached_count=len(cached),
                fetched_count=0,
            )

        self._client.initialize()
        self._client.ensure_symbol_selected(query.symbol)
        rates = self._client.rates_range(
            query.symbol,
            self._client.timeframe_value(query.timeframe.value),
            from_time,
            to_time,
        )
        fetched = [self._to_candle(rate) for rate in rates]
        if not fetched:
            return CandleResponse(
                symbol=query.symbol,
                timeframe=query.timeframe,
                **{"from": from_time, "to": to_time},
                candles=cached,
                cached_count=len(cached),
                fetched_count=0,
            )

        self._repository.upsert_candles(
            self._repository.upsert_symbol(self._symbol(query.symbol)),
            query.timeframe.value,
            fetched,
        )
        candles = self._repository.get_candles(query.symbol, query.timeframe.value, from_time, to_time)
        return CandleResponse(
            symbol=query.symbol,
            timeframe=query.timeframe,
            **{"from": from_time, "to": to_time},
            candles=candles,
            cached_count=len(cached),
            fetched_count=len(fetched),
        )

    def _symbol(self, name: str) -> SymbolResponse:
        symbol = self._client.module.symbol_info(name)
        return SymbolResponse(
            name=symbol.name,
            description=symbol.description or symbol.name,
            path=symbol.path or "",
            digits=int(symbol.digits),
            point=float(symbol.point),
            visible=bool(symbol.visible),
        )

    def _to_candle(self, rate: Any) -> MarketCandle:
        return MarketCandle(
            time=self._client.utc_datetime(int(rate["time"])),
            open=float(rate["open"]),
            high=float(rate["high"]),
            low=float(rate["low"]),
            close=float(rate["close"]),
            tick_volume=float(rate["tick_volume"]),
            spread=float(rate["spread"]),
            real_volume=float(rate["real_volume"]),
        )
