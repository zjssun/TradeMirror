from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.database.models import ImportBatch
from app.database.repositories.trade_repository import TradeRepository
from app.importer.csv_reader import parse_csv
from app.importer.field_detector import detect_mapping, validate_mapping
from app.importer.trade_normalizer import fingerprint, parse_direction, parse_number, parse_time
from app.schemas.importer import ImportResult, PreviewResponse, RowIssue


class ImportService:
    def __init__(self, database, temp_dir: Path) -> None:
        self._database = database
        self._temp_dir = temp_dir

    def preview(self, filename: str, content: bytes) -> PreviewResponse:
        if len(content) > 50 * 1024 * 1024:
            raise ValueError("CSV 文件不能超过 50 MB。")
        columns, rows, encoding, delimiter = parse_csv(content)
        preview_id = uuid.uuid4().hex
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        (self._temp_dir / f"{preview_id}.csv").write_bytes(content)
        return PreviewResponse(preview_id=preview_id, filename=filename, encoding=encoding, delimiter=delimiter, columns=columns, mappings=detect_mapping(columns), sample_rows=rows[:50], timezone_hint="UTC" if any(column.endswith("_utc") for column in columns) else None)

    def commit(self, preview_id: str, filename: str, mapping: dict[str, str], timezone: str) -> ImportResult:
        path = self._temp_dir / f"{preview_id}.csv"
        if not path.exists():
            raise ValueError("导入预览已过期，请重新选择 CSV 文件。")
        content = path.read_bytes()
        columns, rows, encoding, delimiter = parse_csv(content)
        validate_mapping(mapping, columns)
        issues: list[RowIssue] = []
        normalized = []
        utc_hint = timezone == "UTC" or any(source.endswith("_utc") for source in mapping.values())
        for number, row in enumerate(rows, start=2):
            try:
                trade = self._normalize(row, mapping, utc_hint)
                normalized.append(trade)
            except ValueError as error:
                issues.append(RowIssue(row_number=number, message=str(error)))
        batch = ImportBatch(source_filename=filename, source_hash=hashlib.sha256(content).hexdigest(), encoding=encoding, delimiter=delimiter, mapping=mapping, timezone="UTC" if utc_hint else timezone, status="completed", total_rows=len(rows), imported_rows=0, error_rows=len(issues), duplicate_rows=0, error_summary="; ".join(issue.message for issue in issues[:10]) or None, completed_at=datetime.now(UTC))
        batch_id, duplicate = TradeRepository(self._database).import_trades(batch, normalized)
        path.unlink(missing_ok=True)
        return ImportResult(batch_id=batch_id, total_rows=len(rows), imported_rows=len(normalized) - duplicate, duplicate_rows=duplicate, error_rows=len(issues), issues=issues[:100])

    @staticmethod
    def _normalize(row: dict[str, str], mapping: dict[str, str], utc_hint: bool) -> dict:
        value = lambda field: row.get(mapping.get(field, ""), "")
        open_time, close_time = parse_time(value("open_time"), utc_hint), parse_time(value("close_time"), utc_hint)
        if close_time <= open_time:
            raise ValueError("平仓时间必须晚于开仓时间。")
        open_price, close_price, volume = parse_number(value("open_price"), "开仓价格"), parse_number(value("close_price"), "平仓价格"), parse_number(value("volume"), "交易量")
        if open_price <= 0 or close_price <= 0 or volume <= 0:
            raise ValueError("价格和交易量必须大于零。")
        profit = parse_number(value("profit"), "盈亏")
        commission = parse_number(value("commission"), "手续费", required=False) or 0
        swap = parse_number(value("swap"), "隔夜费", required=False) or 0
        trade = {"source": "CSV", "ticket": value("ticket"), "symbol": value("symbol"), "direction": parse_direction(value("direction")), "open_time": open_time, "close_time": close_time, "open_price": open_price, "close_price": close_price, "volume": volume, "profit": profit, "commission": commission, "swap": swap, "net_profit": profit + commission + swap, "stop_loss": parse_number(value("stop_loss"), "止损", required=False), "take_profit": parse_number(value("take_profit"), "止盈", required=False), "close_reason": value("close_reason") or None}
        if not trade["ticket"] or not trade["symbol"]:
            raise ValueError("订单号和交易品种不能为空。")
        trade["source_fingerprint"] = fingerprint(trade)
        return trade
