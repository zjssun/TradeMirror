from fastapi import APIRouter

from app.api.routes.analysis import batch_router as analysis_batch_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.datasources import router as datasources_router
from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.indicators import router as indicators_router
from app.api.routes.insights import router as insights_router
from app.api.routes.market import router as market_router
from app.api.routes.mt5 import router as mt5_router
from app.api.routes.narratives import router as narratives_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.trades import router as trades_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(mt5_router)
api_router.include_router(market_router)
api_router.include_router(datasources_router)
api_router.include_router(indicators_router)
api_router.include_router(insights_router)
api_router.include_router(narratives_router)
api_router.include_router(preferences_router)
api_router.include_router(trades_router)
api_router.include_router(analysis_router)
api_router.include_router(analysis_batch_router)
api_router.include_router(exports_router)
