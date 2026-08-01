from datetime import UTC, datetime, timedelta
from pathlib import Path
import zipfile

from app.exporter.statistics import calculate_statistics
from app.exporter.tmf_validator import validate_tmf


def sample_trade(profit: float, symbol: str = "EURUSD") -> dict:
    return {"id": 1, "symbol": symbol, "direction": "BUY", "net_profit": profit, "holding_duration_seconds": 3600}


def test_statistics_handles_zero_loss_denominator() -> None:
    statistics = calculate_statistics([sample_trade(10), sample_trade(0)])

    assert statistics["profit_factor"] is None
    assert statistics["win_rate"] == 0.5


def test_tmf_validator_accepts_generated_archive(tmp_path: Path) -> None:
    from app.exporter.tmf_service import TmfExportService
    from app.database.session import create_database_engine
    from app.database.models import Base

    engine = create_database_engine(tmp_path / "trademirror.db")
    from app.database.models import ImportBatch, Trade
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        batch = ImportBatch(source_filename="test.csv", source_hash="x", encoding="utf-8", delimiter=",", mapping={}, timezone="UTC", status="completed", total_rows=1, imported_rows=1, error_rows=0, duplicate_rows=0)
        session.add(batch)
        session.flush()
        session.add(Trade(import_batch_id=batch.id, ticket="1", symbol="EURUSD", direction="BUY", open_time=datetime(2025, 1, 1, tzinfo=UTC), close_time=datetime(2025, 1, 1, 1, tzinfo=UTC), open_price=1.1, close_price=1.2, volume=0.1, profit=10, commission=0, swap=0, net_profit=10, source_fingerprint="test"))
        session.commit()
    from app.schemas.export import TmfExportRequest
    output = TmfExportService(engine, tmp_path).create(TmfExportRequest(trade_ids=[1], include_charts=True))
    path = tmp_path / "exports" / f"{output['export_id']}.tmf"

    assert validate_tmf(path)["passed"] is True
    with zipfile.ZipFile(path) as archive:
        assert "charts/trade-1.png" in archive.namelist()
        assert "trade_events.json" in archive.namelist()
        assert "trading_narrative.md" in archive.namelist()
        assert "trading_timeline.json" in archive.namelist()
        assert '"source": "CSV"' in archive.read("trades.json").decode()
        assert '"source": "CSV"' in archive.read("trade_events.json").decode()
        assert '"symbols": [' in archive.read("manifest.json").decode()
        assert "ticket" not in archive.read("trades.json").decode()
