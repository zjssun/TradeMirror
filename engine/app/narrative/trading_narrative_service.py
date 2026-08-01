from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.engine import Engine

from app.analyzer.timeframe_selector import select_timeframe
from app.database.repositories.trade_context_repository import TradeContextRepository
from app.database.repositories.trade_repository import TradeRepository
from app.events.trade_event_generator import TradeEventGenerator
from app.mt5.market_data_service import MarketDataService
from app.mt5.client import Mt5ClientError
from app.schemas.market import CandleQuery, CandleTimeframe, MarketCandle
from app.schemas.narrative import TradingNarrativeRequest, TradingNarrativeResponse


class TradingNarrativeService:
    def __init__(self, database: Engine, market_service: MarketDataService) -> None:
        self._database = database
        self._market_service = market_service

    def generate(self, request: TradingNarrativeRequest, trades: list[Any] | None = None) -> TradingNarrativeResponse:
        if trades is None:
            trades = TradeRepository(self._database).get_for_narrative(
                request.symbol,
                request.direction,
                request.source,
                request.from_time,
                request.to_time,
            )
        filters = request.model_dump(mode="json")
        if not trades:
            return TradingNarrativeResponse(
                filters=filters,
                trade_count=0,
                narrative="## 交易过程叙事\n\n所选时间范围内没有符合条件的已平仓交易，因此无法重建交易过程。",
                timeline=[],
                markets=[],
                diagnostics=[],
            )

        contexts = TradeContextRepository(self._database).get_many([trade.id for trade in trades])
        by_symbol: dict[str, list[Any]] = defaultdict(list)
        for trade in trades:
            by_symbol[trade.symbol].append(trade)

        timeline: list[dict[str, Any]] = []
        markets: list[dict[str, Any]] = []
        diagnostics: list[str] = []
        for symbol in sorted(by_symbol):
            symbol_trades = sorted(by_symbol[symbol], key=lambda item: (self._utc(item.open_time), self._utc(item.close_time), item.id))
            market = self._market_summary(symbol, symbol_trades, request.from_time, request.to_time)
            markets.append(market)
            diagnostics.extend(market["diagnostics"])
            timeline.extend(self._events(symbol_trades, contexts, market["phases"], request.from_time, request.to_time))

        timeline.sort(key=lambda item: (item["time"], 0 if item["type"] == "open" else 1, item["trade_id"]))
        narrative = self._render(request, timeline, markets, diagnostics)
        return TradingNarrativeResponse(
            filters=filters,
            trade_count=len(trades),
            narrative=narrative,
            timeline=timeline,
            markets=markets,
            diagnostics=diagnostics,
        )

    def _market_summary(self, symbol: str, trades: list[Any], from_time: datetime, to_time: datetime) -> dict[str, Any]:
        timeframe = self._timeframe(trades, from_time, to_time)
        start = min(self._utc(from_time), min(self._utc(trade.open_time) for trade in trades))
        end = max(self._utc(to_time), max(self._utc(trade.close_time) for trade in trades))
        padding = self._duration(timeframe) * 3
        query = CandleQuery(symbol=symbol, timeframe=timeframe, **{"from": start - padding, "to": end + padding})
        diagnostics: list[str] = []
        candles: list[MarketCandle] = []
        try:
            response = self._market_service.get_candles(query)
            candles = response.candles
        except Mt5ClientError as error:
            diagnostics.append(f"{symbol}：无法读取 K 线（{error}）。")
        if not candles:
            diagnostics.append(f"{symbol}：所选范围没有可用 K 线，交易动作仍按订单数据描述。")
        return {
            "symbol": symbol,
            "timeframe": timeframe.value,
            "from_time": start,
            "to_time": end,
            "candle_count": len(candles),
            "phases": self._phases(candles),
            "diagnostics": diagnostics,
        }

    def _events(self, trades: list[Any], contexts: dict[int, Any], phases: list[dict[str, Any]], from_time: datetime, to_time: datetime) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        open_count: dict[tuple[str, str], int] = defaultdict(int)
        for trade in trades:
            event = TradeEventGenerator.generate(trade, contexts.get(trade.id))
            key = (trade.symbol, trade.direction)
            opened_before_range = self._utc(trade.open_time) < self._utc(from_time)
            closed_after_range = self._utc(trade.close_time) > self._utc(to_time)
            prior = open_count[key]
            open_count[key] += 1
            events.append({
                "type": "open", "trade_id": trade.id, "time": self._utc(trade.open_time), "symbol": trade.symbol,
                "direction": trade.direction, "price": trade.open_price, "volume": trade.volume, "source": trade.source,
                "action": "加仓" if prior else "开仓", "phase": self._phase_at(phases, self._utc(trade.open_time)),
                "outside_selected_range": opened_before_range,
            })
            events.append({
                "type": "close", "trade_id": trade.id, "time": self._utc(trade.close_time), "symbol": trade.symbol,
                "direction": trade.direction, "price": trade.close_price, "volume": trade.volume, "source": trade.source,
                "action": "平仓", "net_profit": trade.net_profit,
                "holding_duration_seconds": int((trade.close_time - trade.open_time).total_seconds()),
                "phase": self._phase_at(phases, self._utc(trade.close_time)),
                "outside_selected_range": closed_after_range,
                "context_status": event.context_status,
            })
        return events

    @staticmethod
    def _timeframe(trades: list[Any], from_time: datetime, to_time: datetime) -> CandleTimeframe:
        duration = TradingNarrativeService._utc(to_time) - TradingNarrativeService._utc(from_time)
        if duration <= timedelta(days=2):
            return CandleTimeframe.M15
        if duration <= timedelta(days=14):
            return CandleTimeframe.H1
        return CandleTimeframe.H4

    @staticmethod
    def _duration(timeframe: CandleTimeframe) -> timedelta:
        return {CandleTimeframe.M15: timedelta(minutes=15), CandleTimeframe.H1: timedelta(hours=1), CandleTimeframe.H4: timedelta(hours=4)}[timeframe]

    @staticmethod
    def _phases(candles: list[MarketCandle]) -> list[dict[str, Any]]:
        if not candles:
            return []
        phases: list[dict[str, Any]] = []
        chunk_size = max(1, min(24, len(candles) // 4 or 1))
        for offset in range(0, len(candles), chunk_size):
            chunk = candles[offset:offset + chunk_size]
            first, last = chunk[0], chunk[-1]
            change = (last.close - first.open) / first.open if first.open else 0
            high, low = max(item.high for item in chunk), min(item.low for item in chunk)
            amplitude = (high - low) / first.open if first.open else 0
            trend = "上涨" if change >= 0.002 else "下跌" if change <= -0.002 else "震荡"
            phases.append({"from_time": first.time, "to_time": last.time, "trend": trend, "open": first.open, "close": last.close, "high": high, "low": low, "change_percent": round(change * 100, 3), "amplitude_percent": round(amplitude * 100, 3)})
        return phases

    @staticmethod
    def _phase_at(phases: list[dict[str, Any]], value: datetime) -> dict[str, Any] | None:
        for phase in phases:
            if phase["from_time"] <= value <= phase["to_time"]:
                return phase
        return None

    def _render(self, request: TradingNarrativeRequest, timeline: list[dict[str, Any]], markets: list[dict[str, Any]], diagnostics: list[str]) -> str:
        lines = ["## 交易过程叙事", "", f"时间范围：{self._utc(request.from_time):%Y-%m-%d %H:%M} 至 {self._utc(request.to_time):%Y-%m-%d %H:%M} UTC。", f"已纳入 {len({item['trade_id'] for item in timeline})} 笔已平仓交易，覆盖 {len(markets)} 个品种。", "", "### 行情阶段"]
        for market in markets:
            lines.append(f"- **{market['symbol']}**：使用 {market['timeframe']} K 线，共 {market['candle_count']} 根。")
            for phase in market["phases"]:
                lines.append(f"  - {phase['from_time']:%m-%d %H:%M} 至 {phase['to_time']:%m-%d %H:%M}：{phase['trend']}，价格 {phase['open']:.5g} → {phase['close']:.5g}（{phase['change_percent']:+.3f}%），区间 {phase['low']:.5g}–{phase['high']:.5g}。")
        lines.extend(["", "### 交易动作时间线"])
        for item in timeline:
            phase = item["phase"]
            phase_text = f"，处于{phase['trend']}阶段" if phase else "，对应时点缺少 K 线阶段"
            boundary = "（超出所选范围边界）" if item["outside_selected_range"] else ""
            if item["type"] == "open":
                lines.append(f"- {item['time']:%Y-%m-%d %H:%M}：{item['symbol']} {item['direction']} {item['action']}，价格 {item['price']:.5g}，数量 {item['volume']:.5g}{phase_text}{boundary}。")
            else:
                result = "盈利" if item["net_profit"] >= 0 else "亏损"
                lines.append(f"- {item['time']:%Y-%m-%d %H:%M}：{item['symbol']} {item['direction']} 平仓，价格 {item['price']:.5g}，{result} {item['net_profit']:.2f}，持仓 {self._holding(item['holding_duration_seconds'])}{phase_text}{boundary}。")
        lines.extend(["", "### 供 AI 继续分析", "请依据以上可验证的行情与订单时序，评估交易执行与风险管理；不要把数据未显示的主观动机视为事实。"])
        if diagnostics:
            lines.extend(["", "### 数据限制", *[f"- {item}" for item in diagnostics]])
        return "\n".join(lines)

    @staticmethod
    def _holding(seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        minutes = remainder // 60
        return f"{hours}小时{minutes}分钟" if hours else f"{minutes}分钟"

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
