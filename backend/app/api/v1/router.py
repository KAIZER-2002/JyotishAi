from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.astrology import router as astrology_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.conversations import router as conversations_router
from app.api.v1.routes.documents import router as documents_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(auth_router)
api_router.include_router(astrology_router)
from app.api.v1.routes.astrology_analysis import router as astrology_analysis_router

# astrology_analysis_router intentionally excluded from production routing.
# The /astrology/analysis endpoint is incomplete (see astrology_analysis.py).
# Re-include once: yoga detection, interpretations, and response serialisation are finished.
api_router.include_router(astrology_analysis_router)
api_router.include_router(users_router)
api_router.include_router(conversations_router)
api_router.include_router(documents_router)
