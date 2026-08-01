from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import DataSourceSync, ImportBatch, Trade, TradeContextRecord


class TradeRepository:
    def __init__(self, database) -> None:
        self._database = database

    def import_trades(self, batch: ImportBatch, trades: list[dict]) -> tuple[int, int]:
        imported = duplicate = 0
        with Session(self._database) as session:
            session.add(batch)
            session.flush()
            for values in trades:
                values["import_batch_id"] = batch.id
                try:
                    with session.begin_nested():
                        session.add(Trade(**values))
                        session.flush()
                    imported += 1
                except IntegrityError:
                    duplicate += 1
            batch.imported_rows = imported
            batch.duplicate_rows = duplicate
            session.commit()
            return batch.id, duplicate

    def upsert_source_trades(self, source: str, trades: list[dict]) -> tuple[int, int]:
        imported = updated = 0
        with Session(self._database) as session:
            for values in trades:
                values["source"] = source
                fingerprint = values["source_fingerprint"]
                existing = session.scalar(select(Trade).where(Trade.source_fingerprint == fingerprint))
                if existing:
                    for key, value in values.items():
                        setattr(existing, key, value)
                    updated += 1
                else:
                    session.add(Trade(**values))
                    imported += 1
            session.commit()
        return imported, updated

    def record_sync(self, source: str, account_id: str | None, symbol: str | None, from_time: datetime, to_time: datetime, status: str, trade_count: int, diagnostic: str | None = None) -> DataSourceSync:
        with Session(self._database) as session:
            record = DataSourceSync(
                source=source,
                account_id=account_id,
                symbol=symbol,
                from_time=from_time,
                to_time=to_time,
                status=status,
                trade_count=trade_count,
                diagnostic=diagnostic,
                completed_at=datetime.now(UTC),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def latest_sync(self, source: str) -> DataSourceSync | None:
        with Session(self._database) as session:
            return session.scalar(
                select(DataSourceSync)
                .where(DataSourceSync.source == source)
                .order_by(DataSourceSync.completed_at.desc(), DataSourceSync.id.desc())
            )

    def list_trades(self, page: int, page_size: int, symbol: str | None, direction: str | None, source: str | None = None):
        with Session(self._database) as session:
            statement = select(Trade)
            if symbol:
                statement = statement.where(Trade.symbol == symbol)
            if direction:
                statement = statement.where(Trade.direction == direction)
            if source:
                statement = statement.where(Trade.source == source)
            total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
            items = session.scalars(statement.order_by(Trade.close_time.desc()).offset((page - 1) * page_size).limit(page_size)).all()
            return items, total

    def date_range(self):
        with Session(self._database) as session:
            return session.execute(select(func.min(Trade.close_time), func.max(Trade.close_time))).one()

    def get_for_analysis(self, trade_ids: list[int] | None = None, symbol: str | None = None, direction: str | None = None) -> list[Trade]:
        with Session(self._database) as session:
            statement = select(Trade)
            if trade_ids is not None:
                records = session.scalars(statement.where(Trade.id.in_(trade_ids))).all()
                by_id = {record.id: record for record in records}
                return [by_id[trade_id] for trade_id in trade_ids if trade_id in by_id]
            if symbol:
                statement = statement.where(Trade.symbol == symbol)
            if direction:
                statement = statement.where(Trade.direction == direction)
            return session.scalars(statement.order_by(Trade.close_time.desc())).all()

    def get_for_narrative(self, symbol: str | None, direction: str | None, source: str | None, from_time: datetime, to_time: datetime) -> list[Trade]:
        with Session(self._database) as session:
            statement = select(Trade).where(Trade.open_time <= to_time, Trade.close_time >= from_time)
            if symbol:
                statement = statement.where(Trade.symbol == symbol)
            if direction:
                statement = statement.where(Trade.direction == direction)
            if source:
                statement = statement.where(Trade.source == source)
            return session.scalars(statement.order_by(Trade.open_time, Trade.close_time, Trade.id)).all()

    def get_for_export(self, trade_ids: list[int] | None = None, symbol: str | None = None, direction: str | None = None, from_time=None, to_time=None, source: str | None = None) -> list[Trade]:
        with Session(self._database) as session:
            statement = select(Trade)
            if trade_ids is not None:
                records = session.scalars(statement.where(Trade.id.in_(trade_ids))).all()
                by_id = {record.id: record for record in records}
                return [by_id[trade_id] for trade_id in trade_ids if trade_id in by_id]
            if symbol:
                statement = statement.where(Trade.symbol == symbol)
            if direction:
                statement = statement.where(Trade.direction == direction)
            if source:
                statement = statement.where(Trade.source == source)
            if from_time:
                statement = statement.where(Trade.close_time >= from_time)
            if to_time:
                statement = statement.where(Trade.close_time <= to_time)
            return session.scalars(statement.order_by(Trade.close_time.desc())).all()

    def delete_trades(self, trade_ids: list[int]) -> int:
        with Session(self._database) as session:
            session.execute(delete(TradeContextRecord).where(TradeContextRecord.trade_id.in_(trade_ids)))
            result = session.execute(delete(Trade).where(Trade.id.in_(trade_ids)))
            session.commit()
            return result.rowcount

    def get_trade(self, trade_id: int):
        with Session(self._database) as session:
            return session.get(Trade, trade_id)
