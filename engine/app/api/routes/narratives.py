from fastapi import APIRouter, Depends, Request

from app.api.routes.health import require_engine_token
from app.mt5.client import Mt5Client
from app.mt5.market_data_service import MarketDataService
from app.narrative.trading_narrative_service import TradingNarrativeService
from app.schemas.narrative import TradingNarrativeRequest, TradingNarrativeResponse

router = APIRouter(prefix="/narratives", tags=["narratives"], dependencies=[Depends(require_engine_token)])


@router.post("/trading-process", response_model=TradingNarrativeResponse)
def create_trading_process(request: Request, payload: TradingNarrativeRequest) -> TradingNarrativeResponse:
    market_service = MarketDataService(Mt5Client(), request.app.state.database)
    return TradingNarrativeService(request.app.state.database, market_service).generate(payload)
