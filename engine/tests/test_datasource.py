from datetime import UTC, datetime
from types import SimpleNamespace

from app.database.session import create_database_engine
from app.datasource.csv_source import CsvDataSource
from app.datasource.mt5_source import Mt5DataSource
from app.importer.import_service import ImportService
from app.mt5.client import Mt5Client


class FakeMt5:
    TIMEFRAME_H1 = 1

    def initialize(self):
        return True

    def terminal_info(self):
        return SimpleNamespace(path="C:/MT5/terminal64.exe", build=5000, connected=True)

    def account_info(self):
        return SimpleNamespace(login=123, server="Broker-Demo", company="Broker", currency="USD", balance=1000, equity=1005)

    def symbols_get(self):
        return [SimpleNamespace(name="XAUUSD", description="Gold", path="Metals", digits=2, point=0.01, visible=True)]


def test_mt5_datasource_is_recommended_when_connected(tmp_path) -> None:
    source = Mt5DataSource(Mt5Client(FakeMt5()), create_database_engine(tmp_path / "trades.db"))

    status = source.status()
    symbols = source.get_symbols()

    assert status.source == "MT5"
    assert status.available is True
    assert status.recommended is True
    assert symbols.items[0].name == "XAUUSD"


def test_csv_datasource_is_available_as_compatibility_source(tmp_path) -> None:
    database = create_database_engine(tmp_path / "trades.db")
    source = CsvDataSource(database, ImportService(database, tmp_path / "previews"))

    status = source.status()
    trades = source.get_trades(from_time=datetime(2025, 1, 1, tzinfo=UTC))

    assert status.source == "CSV"
    assert status.available is True
    assert status.recommended is False
    assert trades == []
