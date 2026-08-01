from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import TradeContextRecord


class TradeContextRepository:
    def __init__(self, database): self._database = database
    def get(self, trade_id: int):
        with Session(self._database) as session:
            return session.scalar(select(TradeContextRecord).where(TradeContextRecord.trade_id == trade_id).order_by(TradeContextRecord.analyzed_at.desc()))
    def get_many(self, trade_ids: list[int]) -> dict[int, TradeContextRecord]:
        if not trade_ids:
            return {}
        with Session(self._database) as session:
            records = session.scalars(
                select(TradeContextRecord)
                .where(TradeContextRecord.trade_id.in_(trade_ids))
                .order_by(TradeContextRecord.trade_id, TradeContextRecord.analyzed_at.desc())
            ).all()
            latest: dict[int, TradeContextRecord] = {}
            for record in records:
                latest.setdefault(record.trade_id, record)
            return latest

    def save(self, record: TradeContextRecord):
        record.analysis_version = record.analysis_version or "1.0"
        with Session(self._database) as session:
            existing = session.scalar(select(TradeContextRecord).where(TradeContextRecord.trade_id == record.trade_id, TradeContextRecord.analysis_version == record.analysis_version))
            if existing:
                for key, value in record.__dict__.items():
                    if not key.startswith("_") and key != "id": setattr(existing, key, value)
                record = existing
            else: session.add(record)
            session.commit()
            session.refresh(record)
            return record
