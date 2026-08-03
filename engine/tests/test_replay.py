from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.analyzer.trade_replay_service import TradeReplayService
from app.database.models import Trade
from app.database.session import create_database_engine
from app.schemas.market import CandleResponse, MarketCandle
from app.schemas.replay import ReplayQuery
from test_health import create_client


class FakeMarketService:
    def __init__(self) -> None:
        self.queries = []

    def get_candles(self, query):
        self.queries.append(query)
        candle = MarketCandle(
            time=query.from_time,
            open=100,
            high=101,
            low=99,
            close=100,
            tick_volume=1,
            spread=0,
            real_volume=0,
        )
        return CandleResponse(
            symbol=query.symbol,
            timeframe=query.timeframe,
            **{"from": query.from_time, "to": query.to_time},
            candles=[candle],
            cached_count=1,
            fetched_count=0,
        )


def add_trade(database, trade_id: int, symbol: str, opened: datetime, closed: datetime) -> None:
    with Session(database) as session:
        session.add(Trade(
            id=trade_id,
            source="MT5",
            ticket=str(trade_id),
            symbol=symbol,
            direction="BUY",
            open_time=opened,
            close_time=closed,
            open_price=100,
            close_price=101,
            volume=1,
            profit=1,
            commission=0,
            swap=0,
            net_profit=1,
            source_fingerprint=f"replay-{trade_id}",
        ))
        session.commit()


def test_replay_symbols_require_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/market/replay/symbols")

    assert response.status_code == 401


def test_replay_symbols_and_range_are_based_on_trade_lifecycle(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    add_trade(database, 1, "EURUSD", opened, opened + timedelta(hours=2))
    add_trade(database, 2, "EURUSD", opened + timedelta(hours=1), opened + timedelta(hours=4))
    add_trade(database, 3, "XAUUSD", opened, opened + timedelta(hours=1))
    service = TradeReplayService(database, FakeMarketService())

    symbols = service.symbols()
    replay = service.load(ReplayQuery(symbol="EURUSD", **{"from": opened, "to": opened + timedelta(hours=4)}))

    assert [(item.symbol, item.trade_count) for item in symbols] == [("EURUSD", 2), ("XAUUSD", 1)]
    assert [event.trade_id for event in replay.events] == [1, 2]
    assert replay.candle_from < opened
    assert replay.candle_to > opened + timedelta(hours=4)
    assert replay.events[0].net_profit == 1
    database.dispose()


def test_replay_clamps_date_range_to_symbol_trade_span(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    add_trade(database, 1, "EURUSD", opened, opened + timedelta(hours=1))
    service = TradeReplayService(database, FakeMarketService())

    replay = service.load(ReplayQuery(symbol="EURUSD", **{"from": opened - timedelta(hours=10), "to": opened + timedelta(hours=10)}))

    assert replay.from_time == opened
    assert replay.to_time == opened + timedelta(hours=1)
    database.dispose()


def test_replay_rejects_date_range_without_symbol_trades(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    add_trade(database, 1, "EURUSD", opened, opened + timedelta(hours=1))
    service = TradeReplayService(database, FakeMarketService())

    try:
        service.load(ReplayQuery(symbol="EURUSD", **{"from": opened + timedelta(days=1), "to": opened + timedelta(days=2)}))
    except ValueError as error:
        assert "没有" in str(error)
    else:
        raise AssertionError("Expected a range validation error")
    database.dispose()


def test_replay_pre_roll_uses_earliest_overlapping_entry(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    add_trade(database, 1, "EURUSD", opened, opened + timedelta(hours=8))
    service = TradeReplayService(database, FakeMarketService())

    replay = service.load(ReplayQuery(symbol="EURUSD", **{"from": opened + timedelta(hours=2), "to": opened + timedelta(hours=4)}))

    assert replay.candle_from == opened - timedelta(minutes=81)
    assert replay.initial_cursor == 0
    assert replay.available_pre_roll_candles == 0
    assert service._market_service.queries[0].from_time == replay.candle_from
    database.dispose()


def test_replay_defaults_are_consistent_in_schema_and_openapi(tmp_path) -> None:
    assert ReplayQuery.model_fields["pre_roll_candles"].default == 20

    with create_client(tmp_path) as client:
        parameters = client.get("/openapi.json").json()["paths"]["/market/replay"]["get"]["parameters"]

    pre_roll = next(parameter for parameter in parameters if parameter["name"] == "pre_roll_candles")
    assert pre_roll["schema"]["default"] == 20


def test_replay_auto_timeframe_accounts_for_expanded_window(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    closed = opened + timedelta(days=10)
    add_trade(database, 1, "EURUSD", opened, closed)
    market_service = FakeMarketService()
    service = TradeReplayService(database, market_service)

    replay = service.load(ReplayQuery(symbol="EURUSD", **{"from": opened, "to": closed}, pre_roll_candles=500, post_roll_candles=500))

    assert replay.timeframe.value == "M5"
    assert all(query.timeframe.value == "M5" for query in market_service.queries)
    database.dispose()


def test_replay_rejects_expanded_explicit_timeframe_before_loading_candles(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    opened = datetime(2025, 1, 1, 10, tzinfo=UTC)
    closed = opened + timedelta(days=10)
    add_trade(database, 1, "EURUSD", opened, closed)
    market_service = FakeMarketService()
    service = TradeReplayService(database, market_service)

    try:
        service.load(ReplayQuery(symbol="EURUSD", timeframe="M1", **{"from": opened, "to": closed}, pre_roll_candles=500, post_roll_candles=500))
    except ValueError as error:
        assert "5000" in str(error)
    else:
        raise AssertionError("Expected an expanded replay limit error")

    assert market_service.queries == []
    database.dispose()
