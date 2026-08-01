from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.routes.health import require_engine_token
from app.insights.trading_insights_service import TradingInsightsService
from app.schemas.insights import InsightsQuery, InsightsResponse

router = APIRouter(prefix="/insights", tags=["insights"], dependencies=[Depends(require_engine_token)])


@router.get("", response_model=InsightsResponse)
def get_insights(
    request: Request,
    symbol: str | None = Query(default=None, min_length=1, max_length=64),
    direction: str | None = Query(default=None, pattern="^(BUY|SELL)$"),
    from_time: str | None = Query(default=None, alias="from"),
    to_time: str | None = Query(default=None, alias="to"),
) -> InsightsResponse:
    try:
        query = InsightsQuery(symbol=symbol, direction=direction, **{"from": from_time, "to": to_time})
        return TradingInsightsService(request.app.state.database).get(query)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
