from app.routers.chat import router as chat_router
from app.routers.leads import router as leads_router
from app.routers.analytics import router as analytics_router
from app.routers.knowledge import router as knowledge_router
from app.routers.properties import router as properties_router

__all__ = [
    "chat_router",
    "leads_router",
    "analytics_router",
    "knowledge_router",
    "properties_router",
]
