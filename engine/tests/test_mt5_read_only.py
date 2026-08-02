from pathlib import Path


def test_mt5_integration_excludes_trade_execution_apis() -> None:
    app_dir = Path(__file__).parents[1] / "app"
    source = "\n".join(path.read_text(encoding="utf-8") for path in app_dir.rglob("*.py"))

    for forbidden in ("order_send", "order_check", "positions_modify", "order_modify"):
        assert forbidden not in source
