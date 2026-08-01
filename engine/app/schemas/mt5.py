from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Mt5ConnectionState(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNAVAILABLE = "unavailable"


class Mt5Diagnostic(BaseModel):
    code: str
    message: str
    remediation: str


class AccountSummary(BaseModel):
    login: int
    server: str
    company: str | None = None
    currency: str
    balance: float
    equity: float


class TerminalSummary(BaseModel):
    path: str | None = None
    version: str | None = None
    connected: bool


class Mt5StatusResponse(BaseModel):
    state: Mt5ConnectionState
    terminal: TerminalSummary | None = None
    account: AccountSummary | None = None
    diagnostic: Mt5Diagnostic | None = None


class SymbolResponse(BaseModel):
    name: str
    description: str
    path: str
    digits: int
    point: float
    visible: bool


class SymbolListResponse(BaseModel):
    items: list[SymbolResponse]
    total: int
    fetched_at: datetime
