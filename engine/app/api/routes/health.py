from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request

router = APIRouter(tags=["health"])


def require_engine_token(request: Request) -> None:
    request.app.state.require_launch_token(
        request.headers.get("X-TradeMirror-Token")
    )


@router.get("/health", dependencies=[Depends(require_engine_token)])
def get_health(request: Request) -> dict[str, object]:
    return {
        "status": "healthy",
        "engine_version": request.app.version,
        "database": "ready",
        "server_time": datetime.now(UTC).isoformat(),
    }
