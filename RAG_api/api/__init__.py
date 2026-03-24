"""
api package

FastAPI REST API endpoints and models organized by domain.
Provides clean separation between endpoint logic and business logic handled by handlers/.
"""

from .models import (
    ChatRequest,
    ChatResponse, 
    UploadResponse,
    UrlRequest,
    HealthResponse
)
from .endpoints.health import router as health_router
from .endpoints.chat import router as chat_router
from .endpoints.upload import router as upload_router

__all__ = [
    # Models
    "ChatRequest",
    "ChatResponse", 
    "UploadResponse",
    "UrlRequest",
    "HealthResponse",
    # Routers
    "health_router",
    "chat_router", 
    "upload_router"
]