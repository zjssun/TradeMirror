from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.routes.health import require_engine_token
from app.mt5.client import Mt5Client, Mt5ClientError
from app.mt5.market_data_service import MarketDataService
from app.schemas.market import CandleQuery, CandleResponse, CandleTimeframe

router = APIRouter(prefix="/market", tags=["market"], dependencies=[Depends(require_engine_token)])


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
