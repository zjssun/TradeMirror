from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.engine import Engine

from app.analyzer.candle_matcher import timeframe_duration
from app.mt5.client import Mt5Client, Mt5ClientError
from app.mt5.market_data_service import MarketDataService
from app.schemas.market import CANDLES_PER_DAY, MAX_CANDLES_PER_REQUEST, CandleQuery, CandleTimeframe, MarketCandle


class MarketWindowService:
    def __init__(self, database: Engine, client: Mt5Client | None = None) -> None:
        self._service = MarketDataService(client or Mt5Client(), database)

    def load(
        self,
        symbol: str,
        timeframe: CandleTimeframe,
        open_time: datetime,
        close_time: datetime,
    ) -> tuple[list[MarketCandle], int]:
        open_time = open_time.replace(tzinfo=UTC) if open_time.tzinfo is None else open_time.astimezone(UTC)
        close_time = close_time.replace(tzinfo=UTC) if close_time.tzinfo is None else close_time.astimezone(UTC)
        candle_duration = timeframe_duration(timeframe)
        start = open_time - 80 * candle_duration
        end = close_time + 20 * candle_duration
        fetched_count = 0
        candles: dict[datetime, MarketCandle] = {}
        max_chunk_days = min(366, MAX_CANDLES_PER_REQUEST // CANDLES_PER_DAY[timeframe])
        max_chunk = timedelta(days=max_chunk_days)
        current = start
        while current < end:
            chunk_end = min(current + max_chunk, end)
            response = self._service.get_candles(
                CandleQuery(symbol=symbol, timeframe=timeframe, **{"from": current, "to": chunk_end})
            )
            candles.update({candle.time: candle for candle in response.candles})
            fetched_count += response.fetched_count
            current = chunk_end
        return sorted(candles.values(), key=lambda candle: candle.time), fetched_count


__all__ = ["MarketWindowService", "Mt5ClientError"]
