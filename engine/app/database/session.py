from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.database.models import Base


def create_database_engine(database_path: Path) -> Engine:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(engine)
    _upgrade_trade_schema(engine)
    return engine


def _upgrade_trade_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if "trades" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("trades")}
    additions = {
        "source": "VARCHAR(16) NOT NULL DEFAULT 'CSV'",
        "source_trade_id": "VARCHAR(128)",
        "source_position_id": "VARCHAR(128)",
        "source_account_id": "VARCHAR(128)",
        "source_metadata": "JSON",
        "synced_at": "DATETIME",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE trades ADD COLUMN {name} {definition}"))
        connection.execute(text("UPDATE trades SET source = 'CSV' WHERE source IS NULL OR source = ''"))
    import_batch_column = next((column for column in inspect(engine).get_columns("trades") if column["name"] == "import_batch_id"), None)
    if import_batch_column and not import_batch_column["nullable"]:
        _rebuild_trades_with_nullable_import_batch(engine)
    index_columns = [
        ("ix_trades_import_batch_id", "import_batch_id"),
        ("ix_trades_source", "source"),
        ("ix_trades_ticket", "ticket"),
        ("ix_trades_symbol", "symbol"),
        ("ix_trades_direction", "direction"),
        ("ix_trades_open_time", "open_time"),
        ("ix_trades_close_time", "close_time"),
        ("ix_trades_net_profit", "net_profit"),
        ("ix_trades_source_fingerprint", "source_fingerprint"),
    ]
    existing_columns = {column["name"] for column in inspect(engine).get_columns("trades")}
    with engine.begin() as connection:
        for index_name, column in index_columns:
            if column in existing_columns:
                connection.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON trades ({column})"))


def _rebuild_trades_with_nullable_import_batch(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
        connection.commit()
        try:
            with connection.begin():
                connection.execute(text("""
                    CREATE TABLE trades_rebuilt (
                        id INTEGER NOT NULL PRIMARY KEY,
                        import_batch_id INTEGER REFERENCES import_batches(id),
                        source VARCHAR(16) NOT NULL DEFAULT 'CSV',
                        source_trade_id VARCHAR(128),
                        source_position_id VARCHAR(128),
                        source_account_id VARCHAR(128),
                        source_metadata JSON,
                        synced_at DATETIME,
                        ticket VARCHAR(64) NOT NULL,
                        symbol VARCHAR(64) NOT NULL,
                        direction VARCHAR(8) NOT NULL,
                        open_time DATETIME NOT NULL,
                        close_time DATETIME NOT NULL,
                        open_price FLOAT NOT NULL,
                        close_price FLOAT NOT NULL,
                        volume FLOAT NOT NULL,
                        profit FLOAT NOT NULL,
                        commission FLOAT NOT NULL,
                        swap FLOAT NOT NULL,
                        net_profit FLOAT NOT NULL,
                        stop_loss FLOAT,
                        take_profit FLOAT,
                        close_reason VARCHAR(64),
                        source_fingerprint VARCHAR(64) NOT NULL UNIQUE,
                        created_at DATETIME NOT NULL
                    )
                """))
                columns = [column["name"] for column in inspect(engine).get_columns("trades")]
                names = ", ".join(columns)
                connection.execute(text(f"INSERT INTO trades_rebuilt ({names}) SELECT {names} FROM trades"))
                connection.execute(text("DROP TABLE trades"))
                connection.execute(text("ALTER TABLE trades_rebuilt RENAME TO trades"))
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys = ON")
