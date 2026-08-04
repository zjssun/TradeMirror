from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.indicators.schemas import IndicatorName


@dataclass(frozen=True)
class IndicatorDefinition:
    name: IndicatorName
    display_name_zh: str
    display_name_en: str
    pane: Literal["main", "separate"]
    defaults: dict[str, float | int]
    parameter_ranges: dict[str, dict[str, float | int]]
    series_fields: tuple[str, ...]


DEFINITIONS: dict[IndicatorName, IndicatorDefinition] = {
    "SMA": IndicatorDefinition("SMA", "简单移动平均线", "Simple Moving Average", "main", {"period": 20}, {"period": {"min": 2, "max": 500}}, ("value",)),
    "EMA": IndicatorDefinition("EMA", "指数移动平均线", "Exponential Moving Average", "main", {"period": 20}, {"period": {"min": 2, "max": 500}}, ("value",)),
    "BOLLINGER_BANDS": IndicatorDefinition("BOLLINGER_BANDS", "布林带", "Bollinger Bands", "main", {"period": 20, "std_dev": 2.0}, {"period": {"min": 2, "max": 500}, "std_dev": {"min": 0.1, "max": 10.0}}, ("upper", "middle", "lower")),
    "RSI": IndicatorDefinition("RSI", "相对强弱指数", "Relative Strength Index", "separate", {"period": 14}, {"period": {"min": 2, "max": 500}}, ("value",)),
    "MACD": IndicatorDefinition("MACD", "平滑异同移动平均线", "MACD", "separate", {"fast": 12, "slow": 26, "signal": 9}, {"fast": {"min": 2, "max": 200}, "slow": {"min": 3, "max": 500}, "signal": {"min": 2, "max": 200}}, ("macd", "signal", "histogram")),
    "ATR": IndicatorDefinition("ATR", "平均真实波幅", "Average True Range", "separate", {"period": 14}, {"period": {"min": 2, "max": 500}}, ("value",)),
}


def resolve_parameters(name: IndicatorName, supplied: dict[str, float | int]) -> dict[str, float | int]:
    definition = DEFINITIONS[name]
    unknown = set(supplied) - set(definition.defaults)
    if unknown:
        raise ValueError(f"{name} 包含不支持的参数：{', '.join(sorted(unknown))}。")
    parameters = {**definition.defaults, **supplied}
    for key, limits in definition.parameter_ranges.items():
        value = parameters[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not limits["min"] <= value <= limits["max"]:
            raise ValueError(f"{name} 参数 {key} 必须在 {limits['min']} 到 {limits['max']} 之间。")
        if key in {"period", "fast", "slow", "signal"} and int(value) != value:
            raise ValueError(f"{name} 参数 {key} 必须是整数。")
        if key in {"period", "fast", "slow", "signal"}:
            parameters[key] = int(value)
    if name == "MACD" and parameters["fast"] >= parameters["slow"]:
        raise ValueError("MACD 的 fast 必须小于 slow。")
    return parameters


def definitions_response() -> list[dict]:
    return [
        {
            "name": definition.name,
            "display_name": {"zh-CN": definition.display_name_zh, "en-US": definition.display_name_en},
            "pane": definition.pane,
            "defaults": definition.defaults,
            "parameter_ranges": definition.parameter_ranges,
            "series_fields": definition.series_fields,
        }
        for definition in DEFINITIONS.values()
    ]
