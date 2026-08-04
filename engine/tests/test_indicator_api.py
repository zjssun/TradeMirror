from datetime import UTC, datetime, timedelta

from test_health import create_client

TOKEN = {"X-TradeMirror-Token": "test-token"}


def candles(count: int = 80) -> list[dict]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        {
            "time": (start + timedelta(minutes=15 * index)).isoformat(),
            "open": 100 + index * 0.1,
            "high": 101 + index * 0.1,
            "low": 99 + index * 0.1,
            "close": 100.5 + index * 0.1,
            "tick_volume": 1,
            "spread": 0,
            "real_volume": 0,
        }
        for index in range(count)
    ]


def request(indicators: list[dict], source: list[dict] | None = None) -> dict:
    return {"symbol": "EURUSD", "timeframe": "M15", "candles": source or candles(), "indicators": indicators}


def test_indicator_endpoints_require_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        assert client.get("/indicators/definitions").status_code == 401
        assert client.post("/indicators/calculate", json=request([{"name": "EMA", "parameters": {}}])).status_code == 401


def test_indicator_definitions_return_registry_and_provider(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/indicators/definitions", headers=TOKEN)

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "ta"
    assert body["provider_version"]
    assert [item["name"] for item in body["indicators"]] == ["SMA", "EMA", "BOLLINGER_BANDS", "RSI", "MACD", "ATR"]
    assert body["indicators"][0]["defaults"] == {"period": 20}
    assert body["indicators"][3]["pane"] == "separate"
    assert body["indicators"][2]["series_fields"] == ["upper", "middle", "lower"]


def test_indicator_calculation_handles_multiple_moving_averages(tmp_path) -> None:
    indicators = [
        {"name": "SMA", "parameters": {"period": 10}},
        {"name": "SMA", "parameters": {"period": 20}},
        {"name": "EMA", "parameters": {}},
        {"name": "EMA", "parameters": {"period": 50}},
        {"name": "BOLLINGER_BANDS", "parameters": {}},
    ]
    with create_client(tmp_path) as client:
        response = client.post("/indicators/calculate", headers=TOKEN, json=request(indicators))

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["indicators"]] == ["sma-10", "sma-20", "ema-20", "ema-50", "bollinger-bands-20-2"]
    assert body["indicators"][0]["series"][0]["source_index"] == 9
    assert body["indicators"][2]["parameters"] == {"period": 20}
    assert set(body["indicators"][4]["series"]) == {"upper", "middle", "lower"}


def test_indicator_calculation_rejects_normalized_duplicate_and_invalid_values(tmp_path) -> None:
    with create_client(tmp_path) as client:
        duplicate = client.post("/indicators/calculate", headers=TOKEN, json=request([
            {"name": "EMA", "parameters": {}}, {"name": "EMA", "parameters": {"period": 20}},
        ]))
        invalid_parameters = client.post("/indicators/calculate", headers=TOKEN, json=request([
            {"name": "MACD", "parameters": {"fast": 26, "slow": 26, "signal": 9}},
        ]))
        invalid_ohlc = candles(20)
        invalid_ohlc[0]["high"] = 99
        malformed = client.post("/indicators/calculate", headers=TOKEN, json=request([
            {"name": "SMA", "parameters": {"period": 20}},
        ], invalid_ohlc))

    assert duplicate.status_code == 422
    assert "不能重复" in duplicate.json()["detail"][0]["msg"]
    assert invalid_parameters.status_code == 422
    assert "fast" in invalid_parameters.json()["detail"][0]["msg"]
    assert malformed.status_code == 400
    assert "OHLC" in malformed.json()["detail"]
