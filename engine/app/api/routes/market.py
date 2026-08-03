from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.analyzer.trade_replay_service import TradeReplayService
from app.api.routes.health import require_engine_token
from app.mt5.client import Mt5Client, Mt5ClientError
from app.mt5.market_data_service import MarketDataService
from app.schemas.market import CandleQuery, CandleResponse, CandleTimeframe
from app.schemas.replay import ReplayQuery, ReplayResponse, ReplaySymbolOption

router = APIRouter(prefix="/market", tags=["market"], dependencies=[Depends(require_engine_token)])


@router.get("/replay/symbols", response_model=list[ReplaySymbolOption])
def replay_symbols(request: Request) -> list[ReplaySymbolOption]:
    return TradeReplayService(request.app.state.database).symbols()


@router.get("/replay", response_model=ReplayResponse)
def get_replay(
    request: Request,
    symbol: str = Query(min_length=1, max_length=64),
    from_time: datetime = Query(alias="from"),
    to_time: datetime = Query(alias="to"),
    timeframe: CandleTimeframe | None = Query(default=None),
    pre_roll_candles: int = Query(default=20, ge=0, le=500),
    post_roll_candles: int = Query(default=20, ge=0, le=500),
) -> ReplayResponse:
    try:
        query = ReplayQuery(symbol=symbol, timeframe=timeframe, pre_roll_candles=pre_roll_candles, post_roll_candles=post_roll_candles, **{"from": from_time, "to": to_time})
        return TradeReplayService(request.app.state.database).load(query)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Mt5ClientError as error:
        raise HTTPException(
            status_code=503,
            detail={"code": error.code, "message": str(error), "remediation": error.remediation},
        ) from error


@router.get("/candles", response_model=CandleResponse)
def get_candles(
    request: Request,
    symbol: str = Query(min_length=1, max_length=64),
    timeframe: CandleTimeframe = Query(),
    from_time: datetime = Query(alias="from"),
    to_time: datetime = Query(alias="to"),
) -> CandleResponse:
    try:
        query = CandleQuery(
            symbol=symbol,
            timeframe=timeframe,
            **{"from": from_time, "to": to_time},
        )
        return MarketDataService(Mt5Client(), request.app.state.database).get_candles(query)
    except Mt5ClientError as error:
        raise HTTPException(
            status_code=503,
            detail={"code": error.code, "message": str(error), "remediation": error.remediation},
        ) from error
