from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzer.market_window_service import MarketWindowService
from app.database.models import TradeContextRecord
from app.database.repositories.trade_context_repository import TradeContextRepository
from app.analyzer.candle_matcher import split_candles
from app.analyzer.excursion_calculator import excursions
from app.analyzer.timeframe_selector import select_timeframe
from app.schemas.market import CANDLES_PER_DAY, MAX_CANDLES_PER_REQUEST, CandleResponse, CandleTimeframe, MarketCandle
from test_health import create_client


def candle(minutes: int) -> MarketCandle:
    return MarketCandle(
        time=datetime(2025, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes),
        open=100, high=101, low=99, close=100, tick_volume=1, spread=0, real_volume=0,
    )



class RecordedMarketDataService:
    def __init__(self) -> None:
        self.queries = []

    def get_candles(self, query):
        self.queries.append(query)
        return CandleResponse(
            symbol=query.symbol,
            timeframe=query.timeframe,
            **{"from": query.from_time, "to": query.to_time},
            candles=[],
            cached_count=0,
            fetched_count=0,
        )



def test_trade_context_save_updates_default_version_record(tmp_path) -> None:
    with create_client(tmp_path) as client:
        repository = TradeContextRepository(client.app.state.database)
        repository.save(
            TradeContextRecord(
                trade_id=1,
                status="insufficient_data",
                timeframe="M5",
                context={},
                error_message="第一次分析",
            )
        )
        repository.save(
            TradeContextRecord(
                trade_id=1,
                status="completed",
                timeframe="M5",
                context={"updated": True},
            )
        )

        with Session(client.app.state.database) as session:
            records = session.scalars(
                select(TradeContextRecord).where(TradeContextRecord.trade_id == 1)
            ).all()

    assert len(records) == 1
    assert records[0].analysis_version == "1.0"
    assert records[0].status == "completed"
    assert records[0].context == {"updated": True}


def test_market_window_splits_long_m15_requests_within_candle_limit(tmp_path) -> None:
    with create_client(tmp_path) as client:
        service = MarketWindowService(client.app.state.database)
        recorded = RecordedMarketDataService()
        service._service = recorded
        opened = datetime(2025, 1, 1, tzinfo=UTC)

        service.load("EURUSD", CandleTimeframe.M15, opened, opened + timedelta(days=120))

    assert len(recorded.queries) > 1
    assert all(
        (query.to_time - query.from_time).total_seconds() / 86_400
        * CANDLES_PER_DAY[query.timeframe]
        <= MAX_CANDLES_PER_REQUEST
        for query in recorded.queries
    )


def test_select_timeframe_thresholds() -> None:
    opened = datetime(2025, 1, 1, tzinfo=UTC)
    assert select_timeframe(opened, opened + timedelta(hours=4)) is CandleTimeframe.M5
    assert select_timeframe(opened, opened + timedelta(hours=4, seconds=1)) is CandleTimeframe.M15
    assert select_timeframe(opened, opened + timedelta(days=2)) is CandleTimeframe.M15
    assert select_timeframe(opened, opened + timedelta(days=14)) is CandleTimeframe.H1
    assert select_timeframe(opened, opened + timedelta(days=14, seconds=1)) is CandleTimeframe.H4


def test_split_candles_excludes_entry_candle_from_indicators() -> None:
    opened = datetime(2025, 1, 1, 1, 0, tzinfo=UTC)
    closed = opened + timedelta(minutes=10)
    windows = split_candles([candle(index * 5) for index in range(16)], CandleTimeframe.M5, opened, closed)

    assert [item.time for item in windows.pre] == [candle(index * 5).time for index in range(12)]
    assert [item.time for item in windows.holding] == [opened, opened + timedelta(minutes=5)]
    assert [item.time for item in windows.post] == [closed, closed + timedelta(minutes=5)]


def test_datasource_status_requires_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/datasources")

    assert response.status_code == 401


def test_datasource_status_includes_mt5_and_csv(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/datasources", headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 200
    assert {item["source"] for item in response.json()} == {"MT5", "CSV"}


def test_trade_date_range_requires_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/trades/date-range")

    assert response.status_code == 401


def test_trade_date_range_is_empty_without_trades(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/trades/date-range", headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 200
    assert response.json() == {"from_time": None, "to_time": None}


def test_analysis_context_requires_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/trades/1/context")

    assert response.status_code == 401


def test_analysis_returns_not_analyzed_for_new_context(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/trades/123/context", headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 200
    assert response.json()["status"] == "not_analyzed"


def test_batch_analysis_requires_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.post("/analysis/trades", json={"trade_ids": [1]})

    assert response.status_code == 401


def test_batch_analysis_rejects_invalid_target(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.post("/analysis/trades", json={"trade_ids": []}, headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 422


def test_batch_analysis_rejects_empty_filter_result(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.post("/analysis/trades", json={"symbol": "EURUSD"}, headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "没有找到符合条件的交易。"


def test_batch_analysis_reports_missing_selected_trade(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.post("/analysis/trades", json={"trade_ids": [123]}, headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "没有找到符合条件的交易。"


def test_narrative_requires_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.post("/narratives/trading-process", json={"from_time": "2025-01-01T00:00:00Z", "to_time": "2025-01-02T00:00:00Z"})

    assert response.status_code == 401


def test_excursions_handles_sell_direction() -> None:
    candles = [
        MarketCandle(time=datetime(2025, 1, 1, tzinfo=UTC), open=100, high=103, low=95, close=99, tick_volume=1, spread=0, real_volume=0),
        MarketCandle(time=datetime(2025, 1, 1, 0, 5, tzinfo=UTC), open=99, high=101, low=99, close=96, tick_volume=1, spread=0, real_volume=0),
    ]

    assert excursions("SELL", 100, candles) == {"mfe_price": 5, "mae_price": 3, "max_drawdown_price": 4}
