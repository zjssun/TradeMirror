from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from app.api.routes.health import require_engine_token
from app.database.repositories.trade_repository import TradeRepository
from app.importer.import_service import ImportService
from app.schemas.importer import ImportCommitRequest, ImportResult, PreviewResponse
from app.schemas.trade import TradeDateRangeResponse, TradeDeleteRequest, TradeDeleteResponse, TradeListResponse, TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"], dependencies=[Depends(require_engine_token)])


def importer(request: Request) -> ImportService:
    return ImportService(request.app.state.database, request.app.state.import_temp_dir)


@router.post("/import/preview", response_model=PreviewResponse)
async def preview_import(request: Request, file: UploadFile = File()) -> PreviewResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="请选择 CSV 文件。")
    try:
        return importer(request).preview(file.filename, await file.read())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/import/commit", response_model=ImportResult)
def commit_import(request: Request, payload: ImportCommitRequest) -> ImportResult:
    try:
        return importer(request).commit(payload.preview_id, payload.filename, payload.mapping, payload.timezone)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=TradeListResponse)
def list_trades(request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), symbol: str | None = None, direction: str | None = None, source: str | None = Query(default=None, pattern="^(MT5|CSV)$")) -> TradeListResponse:
    items, total = TradeRepository(request.app.state.database).list_trades(page, page_size, symbol, direction, source)
    return TradeListResponse(items=[TradeResponse.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/delete", response_model=TradeDeleteResponse)
def delete_selected_trades(request: Request, payload: TradeDeleteRequest) -> TradeDeleteResponse:
    return TradeDeleteResponse(deleted_count=TradeRepository(request.app.state.database).delete_trades(payload.trade_ids))


@router.get("/date-range", response_model=TradeDateRangeResponse)
def trade_date_range(request: Request) -> TradeDateRangeResponse:
    from_time, to_time = TradeRepository(request.app.state.database).date_range()
    return TradeDateRangeResponse(from_time=from_time, to_time=to_time)


@router.delete("/all", response_model=TradeDeleteResponse)
def delete_all_trades(request: Request) -> TradeDeleteResponse:
    return TradeDeleteResponse(deleted_count=TradeRepository(request.app.state.database).delete_all_trades())


@router.delete("/{trade_id}", response_model=TradeDeleteResponse)
def delete_trade(request: Request, trade_id: int) -> TradeDeleteResponse:
    return TradeDeleteResponse(deleted_count=TradeRepository(request.app.state.database).delete_trades([trade_id]))


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(request: Request, trade_id: int) -> TradeResponse:
    trade = TradeRepository(request.app.state.database).get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="未找到交易记录。")
    return TradeResponse.model_validate(trade)
