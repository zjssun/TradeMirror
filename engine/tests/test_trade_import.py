from pathlib import Path
import sqlite3

from sqlalchemy import text

from app.database.session import create_database_engine
from app.importer.import_service import ImportService


def test_legacy_trade_database_is_upgraded_with_csv_source(tmp_path) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, ticket VARCHAR(64))")
        connection.execute("INSERT INTO trades (id, ticket) VALUES (1, 'legacy-ticket')")

    engine = create_database_engine(database_path)
    with engine.connect() as connection:
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(trades)"))}
        source = connection.execute(text("SELECT source FROM trades WHERE id = 1")).scalar_one()
    engine.dispose()

    assert {"source", "source_trade_id", "source_position_id", "source_account_id", "source_metadata", "synced_at"} <= columns
    assert source == "CSV"


def test_legacy_non_nullable_batch_allows_mt5_trade_after_upgrade(tmp_path) -> None:
    database_path = tmp_path / "legacy-not-null.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE import_batches (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, import_batch_id INTEGER NOT NULL, ticket VARCHAR(64), symbol VARCHAR(64), direction VARCHAR(8), open_time DATETIME, close_time DATETIME, open_price FLOAT, close_price FLOAT, volume FLOAT, profit FLOAT, commission FLOAT, swap FLOAT, net_profit FLOAT, stop_loss FLOAT, take_profit FLOAT, close_reason VARCHAR(64), source_fingerprint VARCHAR(64) UNIQUE, created_at DATETIME)")
        connection.execute("INSERT INTO import_batches (id) VALUES (1)")
        connection.execute("INSERT INTO trades VALUES (1, 1, 'csv', 'EURUSD', 'BUY', '2025-01-01', '2025-01-01 01:00', 1, 1.1, 1, 1, 0, 0, 1, NULL, NULL, NULL, 'csv-fingerprint', '2025-01-01')")

    engine = create_database_engine(database_path)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO trades (ticket, symbol, direction, open_time, close_time, open_price, close_price, volume, profit, commission, swap, net_profit, source_fingerprint, created_at, source) VALUES ('mt5', 'XAUUSD', 'BUY', '2025-01-02', '2025-01-02 01:00', 1, 2, 1, 1, 0, 0, 1, 'mt5-fingerprint', '2025-01-02', 'MT5')"))
        rows = connection.execute(text("SELECT ticket, import_batch_id, source FROM trades ORDER BY id")).all()
    engine.dispose()

    assert rows == [("csv", 1, "CSV"), ("mt5", None, "MT5")]


    trade = ImportService._normalize(
        {
            "ticket": "1", "symbol": "EURUSD", "direction": "BUY",
            "open_time": "2025-01-01T00:00:00Z", "close_time": "2025-01-01T01:00:00Z",
            "open_price": "1.1", "close_price": "1.2", "volume": "0.1", "profit": "10",
        },
        {
            "ticket": "ticket", "symbol": "symbol", "direction": "direction",
            "open_time": "open_time", "close_time": "close_time", "open_price": "open_price",
            "close_price": "close_price", "volume": "volume", "profit": "profit",
        },
        True,
    )

    assert trade["source"] == "CSV"


def test_exness_csv_preview_and_deduplicated_import() -> None:
    source = Path(__file__).parents[2] / "docs" / "01_07_2026-11_07_2026.csv"
    if not source.exists():
        return

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        root = Path(directory)
        database = create_database_engine(root / "trades.db")
        service = ImportService(database, root / "previews")
        preview = service.preview(source.name, source.read_bytes())
        mapping = {item.target: item.source for item in preview.mappings if item.source}

        result = service.commit(preview.preview_id, preview.filename, mapping, "UTC")
        duplicate_preview = service.preview(source.name, source.read_bytes())
        duplicate = service.commit(duplicate_preview.preview_id, duplicate_preview.filename, mapping, "UTC")
        database.dispose()

    assert mapping["open_time"] == "opening_time_utc"
    assert mapping["close_time"] == "closing_time_utc"
    assert result.imported_rows == 396
    assert result.error_rows == 2
    assert duplicate.duplicate_rows == 396
