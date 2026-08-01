from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.market import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_filename: Mapped[str] = mapped_column(String(255))
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    encoding: Mapped[str] = mapped_column(String(32))
    delimiter: Mapped[str] = mapped_column(String(8))
    mapping: Mapped[dict[str, str]] = mapped_column(JSON)
    timezone: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    total_rows: Mapped[int] = mapped_column(Integer)
    imported_rows: Mapped[int] = mapped_column(Integer)
    error_rows: Mapped[int] = mapped_column(Integer)
    duplicate_rows: Mapped[int] = mapped_column(Integer)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataSourceSync(Base):
    __tablename__ = "datasource_syncs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    from_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    to_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), index=True)
    trade_count: Mapped[int] = mapped_column(Integer, default=0)
    diagnostic: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="CSV", index=True)
    source_trade_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_position_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ticket: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    direction: Mapped[str] = mapped_column(String(8), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open_price: Mapped[float] = mapped_column(Float)
    close_price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    profit: Mapped[float] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0)
    swap: Mapped[float] = mapped_column(Float, default=0)
    net_profit: Mapped[float] = mapped_column(Float, index=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
