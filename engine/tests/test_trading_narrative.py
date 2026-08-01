from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.database.models import Trade
from app.database.session import create_database_engine
from app.narrative.trading_narrative_service import TradingNarrativeService
from app.schemas.market import CandleResponse, CandleTimeframe, MarketCandle
from app.schemas.narrative import TradingNarrativeRequest


class FakeMarketService:
    def get_candles(self, query):
        candles = [
            MarketCandle(time=query.from_time + timedelta(hours=index), open=100 + index, high=101 + index, low=99 + index, close=100.5 + index, tick_volume=1, spread=0, real_volume=0)
            for index in range(6)
        ]
        return CandleResponse(symbol=query.symbol, timeframe=query.timeframe, **{"from": query.from_time, "to": query.to_time}, candles=candles, cached_count=0, fetched_count=len(candles))


def trade(ticket: str, opened: datetime, closed: datetime, symbol: str = "EURUSD") -> Trade:
    return Trade(import_batch_id=None, source="MT5", ticket=ticket, symbol=symbol, direction="BUY", open_time=opened, close_time=closed, open_price=1.1, close_price=1.2, volume=0.1, profit=10, commission=0, swap=0, net_profit=10, source_fingerprint=f"MT5:test:{ticket}")


def test_narrative_orders_events_and_separates_symbols(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    start = datetime(2025, 1, 1, tzinfo=UTC)
    with Session(database) as session:
        session.add_all([trade("1", start, start + timedelta(hours=2)), trade("2", start + timedelta(hours=1), start + timedelta(hours=3)), trade("3", start, start + timedelta(hours=1), "XAUUSD")])
        session.commit()

    result = TradingNarrativeService(database, FakeMarketService()).generate(TradingNarrativeRequest(from_time=start + timedelta(minutes=30), to_time=start + timedelta(hours=4)))

    assert result.trade_count == 3
    assert [item["symbol"] for item in result.markets] == ["EURUSD", "XAUUSD"]
    assert [item["action"] for item in result.timeline if item["type"] == "open"] == ["开仓", "开仓", "加仓"]
    assert "交易过程叙事" in result.narrative
    assert "超出所选范围边界" in result.narrative


def test_narrative_returns_empty_result(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    start = datetime(2025, 1, 1, tzinfo=UTC)

    result = TradingNarrativeService(database, FakeMarketService()).generate(TradingNarrativeRequest(from_time=start, to_time=start + timedelta(days=1)))

    assert result.trade_count == 0
    assert result.timeline == []
