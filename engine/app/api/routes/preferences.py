from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.routes.health import require_engine_token
from app.database.repositories.application_preference_repository import ApplicationPreferenceRepository
from app.indicators.registry import resolve_parameters
from app.indicators.schemas import IndicatorRequest

router = APIRouter(prefix="/preferences", tags=["preferences"], dependencies=[Depends(require_engine_token)])
_KEY = "indicator_preferences"
_DEFAULTS = [
    {"name": "SMA", "parameters": {"period": 20}, "visible": True},
    {"name": "EMA", "parameters": {"period": 20}, "visible": True},
    {"name": "EMA", "parameters": {"period": 50}, "visible": True},
    {"name": "EMA", "parameters": {"period": 200}, "visible": True},
    {"name": "BOLLINGER_BANDS", "parameters": {"period": 20, "std_dev": 2}, "visible": True},
    {"name": "RSI", "parameters": {"period": 14}, "visible": True},
    {"name": "MACD", "parameters": {"fast": 12, "slow": 26, "signal": 9}, "visible": True},
    {"name": "ATR", "parameters": {"period": 14}, "visible": True},
]


class IndicatorPreferenceItem(IndicatorRequest):
    visible: bool = True


class IndicatorPreferences(BaseModel):
    indicators: list[IndicatorPreferenceItem] = Field(default_factory=list, max_length=12)


def _normalize(payload: IndicatorPreferences) -> dict:
    unique = set()
    indicators = []
    for item in payload.indicators:
        parameters = resolve_parameters(item.name, item.parameters)
        key = (item.name, tuple(sorted(parameters.items())))
        if key in unique:
            raise ValueError("指标不能重复。")
        unique.add(key)
        indicators.append({"name": item.name, "parameters": parameters, "visible": item.visible})
    return {"indicators": indicators}


@router.get("/indicators", response_model=IndicatorPreferences)
def get_indicator_preferences(request: Request) -> dict:
    return ApplicationPreferenceRepository(request.app.state.database).get(_KEY) or {"indicators": _DEFAULTS}


@router.put("/indicators", response_model=IndicatorPreferences)
def save_indicator_preferences(payload: IndicatorPreferences, request: Request) -> dict:
    try:
        normalized = _normalize(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return ApplicationPreferenceRepository(request.app.state.database).save(_KEY, normalized)
