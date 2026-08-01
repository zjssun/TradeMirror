from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    launch_token: str
    data_dir: Path
    log_dir: Path

    @property
    def database_path(self) -> Path:
        return self.data_dir / "trademirror.db"


def _required_environment(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_settings() -> Settings:
    return Settings(
        host=os.environ.get("TRADEMIRROR_HOST", "127.0.0.1"),
        port=int(os.environ.get("TRADEMIRROR_PORT", "8765")),
        launch_token=_required_environment("TRADEMIRROR_LAUNCH_TOKEN"),
        data_dir=Path(_required_environment("TRADEMIRROR_DATA_DIR")),
        log_dir=Path(_required_environment("TRADEMIRROR_LOG_DIR")),
    )
