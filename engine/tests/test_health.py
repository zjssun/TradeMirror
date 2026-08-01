from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def create_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        host="127.0.0.1",
        port=8765,
        launch_token="test-token",
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "logs",
    )
    return TestClient(create_app(settings))


def test_health_rejects_missing_token(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/health")

    assert response.status_code == 401


def test_health_rejects_invalid_token(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/health", headers={"X-TradeMirror-Token": "invalid"})

    assert response.status_code == 401


def test_health_returns_engine_state(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/health", headers={"X-TradeMirror-Token": "test-token"})

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "ready"
    assert (tmp_path / "data" / "trademirror.db").exists()
