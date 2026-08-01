from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import Settings, get_settings
from app.core.logging import configure_logging
from app.database.session import create_database_engine

ENGINE_VERSION = "0.1.0"
logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(settings.log_dir)
        app.state.database = create_database_engine(settings.database_path)
        app.state.data_dir = settings.data_dir
        app.state.import_temp_dir = settings.data_dir / "import-previews"
        logger.info("TradeMirror engine started")
        yield
        app.state.database.dispose()
        logger.info("TradeMirror engine stopped")

    app = FastAPI(
        title="TradeMirror Analysis Engine",
        version=ENGINE_VERSION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:1420", "tauri://localhost"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["X-TradeMirror-Token"],
    )

    def require_launch_token(token: str | None) -> None:
        if not token or not secrets.compare_digest(token, settings.launch_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid engine access token",
            )

    app.state.require_launch_token = require_launch_token
    app.include_router(api_router)
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


app = create_app(
    Settings(
        host="127.0.0.1",
        port=8765,
        launch_token="development-only-token",
        data_dir=Path(".trademirror/data"),
        log_dir=Path(".trademirror/logs"),
    )
)

if __name__ == "__main__":
    run()
