from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Trade
from app.database.session import create_database_engine
from app.mt5.client import Mt5Client
from app.mt5.trade_history_service import TradeHistoryService
from app.schemas.datasource import Mt5HistorySyncRequest


class FakeHistoryMt5:
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_OUT_BY = 3
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    def initialize(self):
        return True

    def account_info(self):
        return SimpleNamespace(login=123456)

    def history_orders_get(self, *_args):
        return []

    def history_deals_get(self, *_args):
        return [
            SimpleNamespace(ticket=101, position_id=500, order=10, entry=0, type=0, symbol="XAUUSD", time=1_735_689_600, price=2000.0, volume=1.0, profit=0.0, commission=0.0, swap=0.0),
            SimpleNamespace(ticket=102, position_id=500, order=11, entry=1, type=1, symbol="XAUUSD", time=1_735_693_200, price=2010.0, volume=0.4, profit=4.0, commission=-0.4, swap=-0.1),
            SimpleNamespace(ticket=103, position_id=500, order=12, entry=1, type=1, symbol="XAUUSD", time=1_735_696_800, price=2020.0, volume=0.6, profit=12.0, commission=-0.6, swap=-0.2),
        ]


def test_mt5_history_sync_all_uses_epoch_start(tmp_path) -> None:
    class FakeAllHistoryMt5(FakeHistoryMt5):
        def __init__(self):
            self.ranges = []

        def history_orders_get(self, from_time, to_time):
            self.ranges.append((from_time, to_time))
            return []

        def history_deals_get(self, from_time, to_time):
            self.ranges.append((from_time, to_time))
            return []

    fake = FakeAllHistoryMt5()
    database = create_database_engine(tmp_path / "trades.db")
    result = TradeHistoryService(Mt5Client(fake), database).sync(
        Mt5HistorySyncRequest(sync_all=True, from_time=datetime(2025, 1, 1, tzinfo=UTC), to_time=datetime(2025, 1, 2, tzinfo=UTC))
    )

    assert result.from_time == datetime(1970, 1, 1, tzinfo=UTC)
    assert all(from_time == datetime(1970, 1, 1, tzinfo=UTC) for from_time, _ in fake.ranges)


def test_mt5_history_sync_allocates_multiple_openings_and_costs(tmp_path) -> None:
    class FakeMultiOpenMt5(FakeHistoryMt5):
        def history_orders_get(self, *_args):
            return [SimpleNamespace(ticket=13, sl=1990.0, tp=2030.0, reason=4)]

        def history_deals_get(self, *_args):
            return [
                SimpleNamespace(ticket=201, position_id=700, order=10, entry=0, type=0, symbol="XAUUSD", time=1_735_689_600, price=2000.0, volume=0.5, profit=0.0, commission=-0.5, swap=-0.1),
                SimpleNamespace(ticket=202, position_id=700, order=11, entry=0, type=0, symbol="XAUUSD", time=1_735_690_000, price=2010.0, volume=0.5, profit=0.0, commission=-0.5, swap=-0.1),
                SimpleNamespace(ticket=203, position_id=700, order=13, entry=1, type=1, symbol="XAUUSD", time=1_735_693_200, price=2020.0, volume=1.0, profit=15.0, commission=-1.0, swap=-0.2),
            ]

    database = create_database_engine(tmp_path / "trades.db")
    service = TradeHistoryService(Mt5Client(FakeMultiOpenMt5()), database)
    result = service.sync(Mt5HistorySyncRequest(from_time=datetime(2025, 1, 1, tzinfo=UTC), to_time=datetime(2025, 1, 2, tzinfo=UTC)))
    with Session(database) as session:
        trade = session.scalar(select(Trade).where(Trade.ticket == "203"))

    assert result.imported_count == 1
    assert trade is not None
    assert trade.open_price == 2005.0
    assert trade.commission == -2.0
    assert trade.swap == -0.4
    assert trade.stop_loss == 1990.0
    assert trade.take_profit == 2030.0
    assert trade.close_reason == "4"


def test_mt5_history_sync_creates_partial_close_trades_idempotently(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    service = TradeHistoryService(Mt5Client(FakeHistoryMt5()), database)
    request = Mt5HistorySyncRequest(
        symbol="XAUUSD",
        from_time=datetime(2025, 1, 1, tzinfo=UTC),
        to_time=datetime(2025, 1, 2, tzinfo=UTC),
    )

    first = service.sync(request)
    second = service.sync(request)
    with Session(database) as session:
        trades = session.scalars(select(Trade).order_by(Trade.ticket)).all()

    assert first.imported_count == 2
    assert first.updated_count == 0
    assert second.imported_count == 0
    assert second.updated_count == 2
    assert [trade.ticket for trade in trades] == ["102", "103"]
    assert [trade.volume for trade in trades] == [0.4, 0.6]
    assert all(trade.source == "MT5" for trade in trades)
    assert all(trade.source_account_id == "123456" for trade in trades)
