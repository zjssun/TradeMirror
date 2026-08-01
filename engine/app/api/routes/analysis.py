from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.routes.health import require_engine_token
from app.analyzer.trade_context_service import TradeContextService
from app.schemas.analysis import BatchAnalyzeRequest, BatchAnalyzeResponse, TradeContextResponse

router = APIRouter(prefix="/trades", tags=["analysis"], dependencies=[Depends(require_engine_token)])
batch_router = APIRouter(prefix="/analysis", tags=["analysis"], dependencies=[Depends(require_engine_token)])

@router.get("/{trade_id}/context", response_model=TradeContextResponse)
def context(request: Request, trade_id: int): return TradeContextService(request.app.state.database).get(trade_id)

@router.post("/{trade_id}/analyze", response_model=TradeContextResponse)
def analyze(request: Request, trade_id: int):
    try: return TradeContextService(request.app.state.database).analyze(trade_id)
    except LookupError as error: raise HTTPException(status_code=404, detail=str(error)) from error


@batch_router.post("/trades", response_model=BatchAnalyzeResponse)
def analyze_many(request: Request, payload: BatchAnalyzeRequest):
    try:
        return TradeContextService(request.app.state.database).analyze_many(payload.trade_ids, payload.symbol, payload.direction)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
