from sqlalchemy.orm import Session

from app.database.models import ApplicationPreference


class ApplicationPreferenceRepository:
    def __init__(self, database) -> None:
        self._database = database

    def get(self, key: str) -> dict | None:
        with Session(self._database) as session:
            record = session.get(ApplicationPreference, key)
            return record.value if record else None

    def save(self, key: str, value: dict) -> dict:
        with Session(self._database) as session:
            record = session.get(ApplicationPreference, key)
            if record:
                record.value = value
            else:
                session.add(ApplicationPreference(key=key, value=value))
            session.commit()
        return value
