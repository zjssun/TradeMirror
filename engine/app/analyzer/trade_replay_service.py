from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.analyzer.candle_matcher import timeframe_duration
from app.database.repositories.trade_repository import TradeRepository
from app.mt5.client import Mt5Client
from app.mt5.market_data_service import MarketDataService
from app.schemas.market import CANDLES_PER_DAY, MAX_CANDLES_PER_REQUEST, CandleQuery, CandleTimeframe
from app.schemas.replay import ReplayQuery, ReplayResponse, ReplaySymbolOption, ReplayTradeEvent

_PRE_CANDLES = 80
_POST_CANDLES = 20
_TIMEFRAMES = (
    CandleTimeframe.M1,
    CandleTimeframe.M5,
    CandleTimeframe.M15,
    CandleTimeframe.M30,
    CandleTimeframe.H1,
    CandleTimeframe.H4,
    CandleTimeframe.D1,
)


class TradeReplayService:
    def __init__(self, database, market_service: MarketDataService | None = None) -> None:
        self._repository = TradeRepository(database)
        self._market_service = market_service or MarketDataService(Mt5Client(), database)

    def symbols(self) -> list[ReplaySymbolOption]:
        return [
            ReplaySymbolOption(
                symbol=symbol,
                available_from=available_from,
                available_to=available_to,
                trade_count=trade_count,
            )
            for symbol, available_from, available_to, trade_count in self._repository.replay_symbols()
        ]

    def load(self, query: ReplayQuery) -> ReplayResponse:
        from_time = query.from_time.astimezone(UTC)
        to_time = query.to_time.astimezone(UTC)
        available_from, available_to = self._repository.replay_span(query.symbol)
        if available_from is None or available_to is None:
            raise ValueError("未找到该品种的交易记录。")
        available_from, available_to = self._utc(available_from), self._utc(available_to)
        if to_time < available_from or from_time > available_to:
            raise ValueError("所选日期范围内没有该品种的交易记录。")
        from_time = max(from_time, available_from)
        to_time = min(to_time, available_to)

        events = [self._event(trade) for trade in self._repository.list_for_replay(query.symbol, from_time, to_time)]
        timeframe = query.timeframe or self._timeframe(from_time, to_time)
        duration = timeframe_duration(timeframe)
        pre_roll_anchor = min((self._utc(event.open_time) for event in events), default=from_time)
        candle_from = pre_roll_anchor - duration * (query.pre_roll_candles + 1)
        candle_to = to_time + duration * query.post_roll_candles
        if events:
            candle_to = max(candle_to, max(self._utc(event.close_time) for event in events))

        candles, cached_count, fetched_count = self._load_candles(query.symbol, timeframe, candle_from, candle_to)
        first_entry = min((self._utc(event.open_time) for event in events), default=None)
        entry_index = -1
        if first_entry:
            for index, candle in enumerate(candles):
                if self._utc(candle.time) > first_entry:
                    break
                entry_index = index
        if entry_index >= 0:
            start_index = max(0, entry_index - query.pre_roll_candles)
            available_pre_roll_candles = entry_index - start_index
            candles = candles[start_index:]
            initial_cursor = available_pre_roll_candles - 1 if available_pre_roll_candles else 0
        else:
            available_pre_roll_candles = 0
            initial_cursor = 0
        return ReplayResponse(
            symbol=query.symbol,
            timeframe=timeframe,
            **{"from": from_time, "to": to_time},
            candle_from=candle_from,
            candle_to=candle_to,
            candles=candles,
            events=events,
            cached_count=cached_count,
            fetched_count=fetched_count,
            pre_roll_candles=query.pre_roll_candles,
            post_roll_candles=query.post_roll_candles,
            selected_trade_count=len(events),
            selected_net_profit=sum(event.net_profit for event in events),
            initial_cursor=initial_cursor,
            available_pre_roll_candles=available_pre_roll_candles,
        )

    def _timeframe(self, from_time: datetime, to_time: datetime) -> CandleTimeframe:
        for timeframe in _TIMEFRAMES:
            duration = timeframe_duration(timeframe)
            expanded_seconds = (to_time - from_time).total_seconds() + (_PRE_CANDLES + _POST_CANDLES) * duration.total_seconds()
            estimated = expanded_seconds / 86_400 * CANDLES_PER_DAY[timeframe]
            if estimated <= MAX_CANDLES_PER_REQUEST:
                return timeframe
        raise ValueError("所选范围过大，无法在回放中加载足够精细的 K 线，请缩短范围。")

    def _load_candles(self, symbol: str, timeframe: CandleTimeframe, from_time: datetime, to_time: datetime):
        max_days = min(366, MAX_CANDLES_PER_REQUEST / CANDLES_PER_DAY[timeframe])
        chunk_duration = timedelta(days=max_days)
        current = from_time
        by_time = {}
        cached_count = fetched_count = 0
        while current < to_time:
            chunk_to = min(current + chunk_duration, to_time)
            response = self._market_service.get_candles(
                CandleQuery(symbol=symbol, timeframe=timeframe, **{"from": current, "to": chunk_to})
            )
            for candle in response.candles:
                by_time[self._utc(candle.time)] = candle
            cached_count += response.cached_count
            fetched_count += response.fetched_count
            current = chunk_to
        return [by_time[key] for key in sorted(by_time)], cached_count, fetched_count

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _event(trade) -> ReplayTradeEvent:
        return ReplayTradeEvent(
            trade_id=trade.id,
            source=trade.source,
            ticket=trade.ticket,
            symbol=trade.symbol,
            direction=trade.direction,
            open_time=trade.open_time,
            close_time=trade.close_time,
            open_price=trade.open_price,
            close_price=trade.close_price,
            volume=trade.volume,
            profit=trade.profit,
            commission=trade.commission,
            swap=trade.swap,
            net_profit=trade.net_profit,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            close_reason=trade.close_reason,
        )
