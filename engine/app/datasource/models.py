from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DataSourceName = Literal["MT5", "CSV"]


@dataclass(frozen=True)
class DataSourceStatus:
    source: DataSourceName
    available: bool
    recommended: bool
    message: str
    remediation: str | None = None
