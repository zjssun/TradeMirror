from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.market import Base


class TradeContextRecord(Base):
    __tablename__ = "trade_contexts"
    __table_args__ = (UniqueConstraint("trade_id", "analysis_version", name="uq_trade_context_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), index=True)
    analysis_version: Mapped[str] = mapped_column(String(16), default="1.0")
    status: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    rsi: Mapped[float | None] = mapped_column(Float, nullable=True)
    atr: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema20: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema50: Mapped[float | None] = mapped_column(Float, nullable=True)
    mfe_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    context: Mapped[dict] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
