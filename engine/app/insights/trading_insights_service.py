from app.database.repositories.trade_context_repository import TradeContextRepository
from app.database.repositories.trade_repository import TradeRepository
from app.exporter.prompt_builder import build_prompt
from app.exporter.statistics import calculate_statistics
from app.exporter.trader_profile import build_profile
from app.schemas.insights import InsightsQuery, InsightsResponse


class TradingInsightsService:
    def __init__(self, database) -> None:
        self._database = database

    def get(self, query: InsightsQuery) -> InsightsResponse:
        trades = TradeRepository(self._database).get_for_export(
            symbol=query.symbol, direction=query.direction, from_time=query.from_time, to_time=query.to_time
        )
        trade_data = [
            {
                "id": trade.id, "symbol": trade.symbol, "direction": trade.direction,
                "net_profit": trade.net_profit,
                "holding_duration_seconds": int((trade.close_time - trade.open_time).total_seconds()),
                "close_time": trade.close_time,
            }
            for trade in trades
        ]
        statistics = calculate_statistics(trade_data)
        profile = build_profile(statistics)
        contexts = TradeContextRepository(self._database).get_many([trade.id for trade in trades])
        completed = sum(record.status == "completed" for record in contexts.values())
        insufficient = sum(record.status == "insufficient_data" for record in contexts.values())
        running = 0.0
        equity_curve = []
        for trade in sorted(trade_data, key=lambda item: item["close_time"]):
            running += trade["net_profit"]
            equity_curve.append({"time": trade["close_time"], "equity": running, "net_profit": trade["net_profit"]})
        manifest = {"options": {"redact_source_identity": False}}
        return InsightsResponse(
            filters={"symbol": query.symbol, "direction": query.direction, "from": query.from_time, "to": query.to_time},
            statistics=statistics,
            profile=profile,
            prompt=build_prompt(manifest, profile, statistics),
            completed_context_count=completed,
            insufficient_data_context_count=insufficient,
            equity_curve=equity_curve,
        )
