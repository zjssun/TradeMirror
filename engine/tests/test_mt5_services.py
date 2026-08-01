from datetime import UTC, datetime
from types import SimpleNamespace

from app.database.session import create_database_engine
from app.mt5.client import Mt5Client
from app.mt5.connection_service import Mt5ConnectionService
from app.mt5.market_data_service import MarketDataService
from app.schemas.market import CandleQuery, CandleTimeframe


class FakeMt5:
    TIMEFRAME_H1 = 1

    def initialize(self):
        return True

    def terminal_info(self):
        return SimpleNamespace(path="C:/MT5/terminal64.exe", build=5000, connected=True)

    def account_info(self):
        return SimpleNamespace(login=123, server="Broker-Demo", company="Broker", currency="USD", balance=1000, equity=1005)

    def symbol_info(self, _name):
        return SimpleNamespace(name="XAUUSD", description="Gold", path="Metals", digits=2, point=0.01, visible=True)

    def copy_rates_range(self, *_args):
        return [{"time": 1_700_000_000, "open": 2000.0, "high": 2010.0, "low": 1995.0, "close": 2005.0, "tick_volume": 100, "spread": 2, "real_volume": 0}]


def test_mt5_connection_status_is_normalized() -> None:
    status = Mt5ConnectionService(Mt5Client(FakeMt5())).connect()

    assert status.state == "connected"
    assert status.account is not None
    assert status.account.login == 123


def test_candles_are_cached(tmp_path) -> None:
    database = create_database_engine(tmp_path / "market.db")
    service = MarketDataService(Mt5Client(FakeMt5()), database)
    query = CandleQuery(
        symbol="XAUUSD",
        timeframe=CandleTimeframe.H1,
        **{"from": datetime(2023, 11, 14, tzinfo=UTC), "to": datetime(2023, 11, 15, tzinfo=UTC)},
    )

    first = service.get_candles(query)
    second = service.get_candles(query)

    assert first.fetched_count == 1
    assert len(second.candles) == 1
