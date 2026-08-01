from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.health import require_engine_token
from app.mt5.client import Mt5Client
from app.mt5.connection_service import Mt5ConnectionService
from app.mt5.symbol_service import SymbolService
from app.schemas.mt5 import Mt5StatusResponse, SymbolListResponse

router = APIRouter(prefix="/mt5", tags=["mt5"], dependencies=[Depends(require_engine_token)])


def connection_service() -> Mt5ConnectionService:
    return Mt5ConnectionService(Mt5Client())


@router.get("/status", response_model=Mt5StatusResponse)
def get_mt5_status() -> Mt5StatusResponse:
    return connection_service().status()


@router.post("/connect", response_model=Mt5StatusResponse)
def connect_mt5() -> Mt5StatusResponse:
    return connection_service().connect()


@router.get("/symbols", response_model=SymbolListResponse)
def get_symbols(
    query: str | None = Query(default=None, max_length=80),
    visible_only: bool = True,
    limit: int = Query(default=200, ge=1, le=500),
) -> SymbolListResponse:
    return SymbolService(Mt5Client()).list_symbols(query, visible_only, limit)
