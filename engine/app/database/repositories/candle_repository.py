from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.database.models import CachedCandle, CachedSymbol
from app.schemas.market import MarketCandle
from app.schemas.mt5 import SymbolResponse


class CandleRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_candles(self, symbol: str, timeframe: str, from_time: datetime, to_time: datetime) -> list[MarketCandle]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(CachedCandle)
                .join(CachedSymbol)
                .where(
                    CachedSymbol.name == symbol,
                    CachedCandle.timeframe == timeframe,
                    CachedCandle.time >= from_time,
                    CachedCandle.time <= to_time,
                )
                .order_by(CachedCandle.time)
            ).all()
            return [self._to_schema(row) for row in rows]

    def upsert_symbol(self, symbol: SymbolResponse) -> int:
        statement = insert(CachedSymbol).values(**symbol.model_dump()).on_conflict_do_update(
            index_elements=[CachedSymbol.name],
            set_={
                "description": symbol.description,
                "path": symbol.path,
                "digits": symbol.digits,
                "point": symbol.point,
                "visible": symbol.visible,
            },
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
            return connection.execute(
                select(CachedSymbol.id).where(CachedSymbol.name == symbol.name)
            ).scalar_one()

    def upsert_candles(self, symbol_id: int, timeframe: str, candles: list[MarketCandle]) -> None:
        if not candles:
            return
        values = [{"symbol_id": symbol_id, "timeframe": timeframe, **candle.model_dump()} for candle in candles]
        statement = insert(CachedCandle).values(values).on_conflict_do_update(
            index_elements=[CachedCandle.symbol_id, CachedCandle.timeframe, CachedCandle.time],
            set_={column: getattr(insert(CachedCandle).excluded, column) for column in ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)

    @staticmethod
    def _to_schema(candle: CachedCandle) -> MarketCandle:
        return MarketCandle(
            time=candle.time.replace(tzinfo=UTC),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            tick_volume=candle.tick_volume,
            spread=candle.spread,
            real_volume=candle.real_volume,
        )
