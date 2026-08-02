from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.routes.health import require_engine_token
from app.exporter.tmf_service import TmfExportService
from app.schemas.export import TmfExportRequest, TmfExportResponse

router = APIRouter(prefix="/exports", tags=["exports"], dependencies=[Depends(require_engine_token)])


@router.post("/tmf", response_model=TmfExportResponse)
def create_tmf(request: Request, payload: TmfExportRequest) -> TmfExportResponse:
    try:
        return TmfExportService(request.app.state.database, request.app.state.tmf_dir).create(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{export_id}/download")
def download_tmf(request: Request, export_id: str):
    path = TmfExportService(request.app.state.database, request.app.state.tmf_dir).path_for(export_id)
    if not path:
        raise HTTPException(status_code=404, detail="未找到导出文件。")
    return FileResponse(path, media_type="application/zip", filename=f"{export_id}.tmf")
