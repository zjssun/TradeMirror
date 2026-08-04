from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.health import require_engine_token
from app.indicators.calculator import IndicatorCalculator
from app.indicators.providers.ta_provider import TaIndicatorProvider
from app.indicators.registry import definitions_response
from app.indicators.schemas import IndicatorCalculationRequest, IndicatorCalculationResponse

router = APIRouter(prefix="/indicators", tags=["indicators"], dependencies=[Depends(require_engine_token)])


def calculator() -> IndicatorCalculator:
    return IndicatorCalculator(TaIndicatorProvider())


@router.get("/definitions")
def get_definitions() -> dict[str, object]:
    engine = calculator()
    return {
        "provider": engine.provider_name,
        "provider_version": engine.provider_version,
        "indicators": definitions_response(),
    }


@router.post("/calculate", response_model=IndicatorCalculationResponse)
def calculate_indicators(payload: IndicatorCalculationRequest) -> IndicatorCalculationResponse:
    try:
        return calculator().calculate(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
