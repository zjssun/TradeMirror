from test_health import create_client

TOKEN = {"X-TradeMirror-Token": "test-token"}


def test_indicator_preferences_require_token(tmp_path) -> None:
    with create_client(tmp_path) as client:
        assert client.get("/preferences/indicators").status_code == 401
        assert client.put("/preferences/indicators", json={"indicators": []}).status_code == 401


def test_indicator_preferences_return_defaults(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.get("/preferences/indicators", headers=TOKEN)

    assert response.status_code == 200
    items = response.json()["indicators"]
    assert [(item["name"], item["parameters"]) for item in items] == [
        ("SMA", {"period": 20}), ("EMA", {"period": 20}), ("EMA", {"period": 50}),
        ("EMA", {"period": 200}), ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2}),
        ("RSI", {"period": 14}), ("MACD", {"fast": 12, "slow": 26, "signal": 9}), ("ATR", {"period": 14}),
    ]
    assert all(item["visible"] is True for item in items)


def test_indicator_preferences_persist_normalized_multiple_mas_and_visibility(tmp_path) -> None:
    payload = {"indicators": [
        {"name": "SMA", "parameters": {"period": 10}, "visible": False},
        {"name": "SMA", "parameters": {"period": 20}, "visible": True},
        {"name": "EMA", "parameters": {}, "visible": True},
        {"name": "EMA", "parameters": {"period": 50}, "visible": False},
    ]}
    with create_client(tmp_path) as client:
        saved = client.put("/preferences/indicators", headers=TOKEN, json=payload)
        restored = client.get("/preferences/indicators", headers=TOKEN)

    assert saved.status_code == 200
    assert restored.status_code == 200
    assert restored.json()["indicators"] == [
        {"name": "SMA", "parameters": {"period": 10}, "visible": False},
        {"name": "SMA", "parameters": {"period": 20}, "visible": True},
        {"name": "EMA", "parameters": {"period": 20}, "visible": True},
        {"name": "EMA", "parameters": {"period": 50}, "visible": False},
    ]


def test_indicator_preferences_reject_normalized_duplicates_without_overwriting_saved_value(tmp_path) -> None:
    saved = {"indicators": [{"name": "EMA", "parameters": {"period": 50}, "visible": True}]}
    duplicate = {"indicators": [
        {"name": "EMA", "parameters": {}, "visible": True},
        {"name": "EMA", "parameters": {"period": 20}, "visible": False},
    ]}
    with create_client(tmp_path) as client:
        assert client.put("/preferences/indicators", headers=TOKEN, json=saved).status_code == 200
        rejected = client.put("/preferences/indicators", headers=TOKEN, json=duplicate)
        restored = client.get("/preferences/indicators", headers=TOKEN)

    assert rejected.status_code == 400
    assert "不能重复" in rejected.json()["detail"]
    assert restored.json() == saved


def test_indicator_preference_put_cors_allows_token_and_json_content(tmp_path) -> None:
    with create_client(tmp_path) as client:
        response = client.options("/preferences/indicators", headers={
            "Origin": "http://localhost:1420",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "X-TradeMirror-Token, Content-Type",
        })

    assert response.status_code == 200
    assert "PUT" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "x-trademirror-token" in response.headers["access-control-allow-headers"].lower()
