from __future__ import annotations

import re

from app.schemas.importer import MappingCandidate

REQUIRED_FIELDS = ("ticket", "symbol", "direction", "open_time", "close_time", "open_price", "close_price", "volume", "profit")
OPTIONAL_FIELDS = ("commission", "swap", "stop_loss", "take_profit", "close_reason")

ALIASES = {
    "ticket": ("ticket", "order", "deal", "订单号", "交易编号"),
    "symbol": ("symbol", "instrument", "品种", "交易品种"),
    "direction": ("type", "side", "direction", "买卖", "方向"),
    "open_time": ("opening_time_utc", "open_time", "opentime", "开仓时间", "开仓日期"),
    "close_time": ("closing_time_utc", "close_time", "closetime", "平仓时间", "平仓日期"),
    "open_price": ("opening_price", "open_price", "price_open", "开仓价"),
    "close_price": ("closing_price", "close_price", "price_close", "平仓价"),
    "volume": ("lots", "volume", "size", "手数"),
    "profit": ("profit", "p/l", "net_profit", "盈亏"),
    "commission": ("commission", "手续费"),
    "swap": ("swap", "隔夜利息"),
    "stop_loss": ("stop_loss", "sl", "止损"),
    "take_profit": ("take_profit", "tp", "止盈"),
    "close_reason": ("close_reason", "reason", "平仓原因"),
}


def normalize(value: str) -> str:
    return re.sub(r"[\s_\-]", "", value).casefold()


def detect_mapping(columns: list[str]) -> list[MappingCandidate]:
    normalized = {normalize(column): column for column in columns}
    candidates = []
    for target in (*REQUIRED_FIELDS, *OPTIONAL_FIELDS):
        source = next((normalized.get(normalize(alias)) for alias in ALIASES[target] if normalize(alias) in normalized), None)
        candidates.append(MappingCandidate(target=target, source=source, confidence="high" if source else "none"))
    return candidates


def validate_mapping(mapping: dict[str, str], columns: list[str]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not mapping.get(field)]
    if missing:
        raise ValueError(f"缺少必填字段映射：{', '.join(missing)}")
    unknown = [source for source in mapping.values() if source not in columns]
    if unknown:
        raise ValueError(f"映射包含不存在的 CSV 列：{', '.join(unknown)}")
    values = list(mapping.values())
    if len(values) != len(set(values)):
        raise ValueError("同一 CSV 列不能映射到多个标准字段。")
