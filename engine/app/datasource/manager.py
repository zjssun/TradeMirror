from __future__ import annotations

from app.datasource.csv_source import CsvDataSource
from app.datasource.mt5_source import Mt5DataSource
from app.datasource.models import DataSourceStatus
from app.importer.import_service import ImportService
from app.mt5.client import Mt5Client


class DataSourceManager:
    def __init__(self, database, import_temp_dir) -> None:
        self._mt5 = Mt5DataSource(Mt5Client(), database)
        self._csv = CsvDataSource(database, ImportService(database, import_temp_dir))

    def status(self) -> list[DataSourceStatus]:
        return [self._mt5.status(), self._csv.status()]

    def default_source(self) -> Mt5DataSource | CsvDataSource:
        return self._mt5 if self._mt5.status().available else self._csv
