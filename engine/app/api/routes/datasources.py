from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.routes.health import require_engine_token
from app.datasource.manager import DataSourceManager
from app.mt5.client import Mt5Client, Mt5ClientError
from app.mt5.trade_history_service import TradeHistoryService
from app.database.repositories.trade_repository import TradeRepository
from app.schemas.datasource import DataSourceStatusResponse, DataSourceSyncResponse, Mt5HistorySyncRequest, Mt5HistorySyncResponse

router = APIRouter(prefix="/datasources", tags=["datasources"], dependencies=[Depends(require_engine_token)])


@router.get("", response_model=list[DataSourceStatusResponse])
def statuses(request: Request) -> list[DataSourceStatusResponse]:
    return [DataSourceStatusResponse(**status.__dict__) for status in DataSourceManager(request.app.state.database, request.app.state.import_temp_dir).status()]


@router.get("/mt5/last-sync", response_model=DataSourceSyncResponse | None)
def latest_mt5_sync(request: Request) -> DataSourceSyncResponse | None:
    record = TradeRepository(request.app.state.database).latest_sync("MT5")
    return DataSourceSyncResponse.model_validate(record) if record else None


@router.post("/mt5/sync", response_model=Mt5HistorySyncResponse)
def sync_mt5_history(request: Request, payload: Mt5HistorySyncRequest) -> Mt5HistorySyncResponse:
    service = TradeHistoryService(Mt5Client(), request.app.state.database)
    try:
        return service.sync(payload)
    except Mt5ClientError as error:
        service.record_failure(payload, str(error))
        raise HTTPException(
            status_code=503,
            detail={"code": error.code, "message": str(error), "remediation": error.remediation},
        ) from error
