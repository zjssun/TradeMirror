from __future__ import annotations

from sqlalchemy.orm import Session

from app.analyzer.candle_matcher import split_candles
from app.analyzer.excursion_calculator import excursions
from app.analyzer.indicator_calculator import indicators
from app.analyzer.market_window_service import MarketWindowService, Mt5ClientError
from app.analyzer.support_resistance import levels
from app.analyzer.timeframe_selector import select_timeframe
from app.analyzer.trend_analyzer import trend
from app.database.models import Trade, TradeContextRecord
from app.database.repositories.trade_context_repository import TradeContextRepository
from app.database.repositories.trade_repository import TradeRepository
from app.schemas.analysis import BatchAnalyzeItem, BatchAnalyzeResponse, TradeContextResponse


class TradeContextService:
    def __init__(self, database): self._database = database
    def get(self, trade_id: int) -> TradeContextResponse:
        record = TradeContextRepository(self._database).get(trade_id)
        if not record: return TradeContextResponse(trade_id=trade_id, status="not_analyzed")
        return TradeContextResponse(trade_id=trade_id, status=record.status, timeframe=record.timeframe if record.status == "completed" else None, **record.context, error_message=record.error_message, analyzed_at=record.analyzed_at)
    def analyze(self, trade_id: int) -> TradeContextResponse:
        with Session(self._database) as session: trade = session.get(Trade, trade_id)
        if not trade: raise LookupError("未找到交易记录。")
        timeframe = select_timeframe(trade.open_time, trade.close_time)
        try:
            candles, fetched_count = MarketWindowService(self._database).load(
                trade.symbol, timeframe, trade.open_time, trade.close_time
            )
        except (Mt5ClientError, ValueError) as error:
            return self._save_insufficient_data(trade, timeframe.value, [], 0, 0, str(error))
        windows = split_candles(candles, timeframe, trade.open_time, trade.close_time)
        if len(windows.pre) < 50 or not windows.holding:
            return self._save_insufficient_data(
                trade,
                timeframe.value,
                windows.pre,
                len(windows.holding),
                fetched_count,
                "缺少分析所需历史K线。请连接 MT5 并加载相应历史范围后重新分析。",
            )
        stats = indicators(windows.pre)
        supports, resistances = levels(windows.pre, trade.open_price)
        execution = {
            "holding_duration_seconds": int((trade.close_time - trade.open_time).total_seconds()),
            **excursions(trade.direction, trade.open_price, windows.holding),
            "net_profit": trade.net_profit,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "close_reason": trade.close_reason,
        }
        context = {
            "data_quality": {
                "required_pre_candles": 50,
                "available_pre_candles": len(windows.pre),
                "available_holding_candles": len(windows.holding),
                "available_post_candles": len(windows.post),
                "fetched_candles": fetched_count,
                "note": "入场指标仅使用开仓前K线；OHLC风险数据为区间近似值。",
            },
            "market_context": {
                **stats,
                "trend": trend(stats, windows.pre),
                "support_levels": supports,
                "resistance_levels": resistances,
            },
            "execution": execution,
            "candles": [c.model_dump(mode="json") for c in [*windows.pre[-30:], *windows.holding, *windows.post]],
        }
        record = TradeContextRecord(
            trade_id=trade.id, status="completed", timeframe=timeframe.value,
            rsi=stats["rsi"], atr=stats["atr"], ema20=stats["ema20"], ema50=stats["ema50"],
            mfe_price=execution["mfe_price"], mae_price=execution["mae_price"],
            max_drawdown_price=execution["max_drawdown_price"], context=context,
        )
        TradeContextRepository(self._database).save(record)
        return self.get(trade_id)

    def analyze_many(self, trade_ids: list[int] | None = None, symbol: str | None = None, direction: str | None = None) -> BatchAnalyzeResponse:
        trades = TradeRepository(self._database).get_for_analysis(trade_ids, symbol, direction)
        if not trades:
            raise ValueError("没有找到符合条件的交易。")
        items: list[BatchAnalyzeItem] = []
        by_id = {trade.id: trade for trade in trades}
        targets = trade_ids if trade_ids is not None else [trade.id for trade in trades]
        for trade_id in targets:
            if trade_id not in by_id:
                items.append(BatchAnalyzeItem(trade_id=trade_id, status="failed", error_message="未找到交易记录。"))
                continue
            try:
                result = self.analyze(trade_id)
                items.append(BatchAnalyzeItem(trade_id=trade_id, status=result.status, error_message=result.error_message))
            except Exception:
                items.append(BatchAnalyzeItem(trade_id=trade_id, status="failed", error_message="分析失败，请检查 MT5 连接和历史行情后重试。"))
        return BatchAnalyzeResponse(
            requested_count=len(items),
            completed_count=sum(item.status == "completed" for item in items),
            insufficient_data_count=sum(item.status == "insufficient_data" for item in items),
            failed_count=sum(item.status == "failed" for item in items),
            items=items,
        )

    def _save_insufficient_data(self, trade, timeframe: str, pre, holding_count: int, fetched_count: int, message: str) -> TradeContextResponse:
        context = {
            "data_quality": {
                "required_pre_candles": 50,
                "available_pre_candles": len(pre),
                "available_holding_candles": holding_count,
                "fetched_candles": fetched_count,
            },
            "market_context": {},
            "execution": {},
            "candles": [candle.model_dump(mode="json") for candle in pre[-30:]],
        }
        TradeContextRepository(self._database).save(
            TradeContextRecord(trade_id=trade.id, status="insufficient_data", timeframe=timeframe, context=context, error_message=message)
        )
        return self.get(trade.id)
