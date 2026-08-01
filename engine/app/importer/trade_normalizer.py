from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.schemas.importer import RowIssue


def parse_direction(value: str) -> str:
    normalized = value.strip().casefold()
    if "buy" in normalized or "买" in normalized:
        return "BUY"
    if "sell" in normalized or "卖" in normalized:
        return "SELL"
    raise ValueError("方向必须是 BUY 或 SELL。")


def parse_number(value: str, field: str, required: bool = True) -> float | None:
    if not value:
        if required:
            raise ValueError(f"{field} 不能为空。")
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError as error:
        raise ValueError(f"{field} 必须是有效数字。") from error


def parse_time(value: str, utc_hint: bool) -> datetime:
    if not value:
        raise ValueError("交易时间不能为空。")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None and utc_hint else parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def fingerprint(values: dict[str, object]) -> str:
    source = "|".join(str(values[field]) for field in ("ticket", "symbol", "direction", "open_time", "close_time", "open_price", "close_price", "volume"))
    return hashlib.sha256(source.encode("utf-8")).hexdigest()
