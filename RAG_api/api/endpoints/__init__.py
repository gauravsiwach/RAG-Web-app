"""
endpoints package

FastAPI router modules organized by functionality.
Each module contains related endpoints for specific domains.
"""

from .health import router as health_router
from .chat import router as chat_router
from .upload import router as upload_router

__all__ = [
    "health_router",
    "chat_router", 
    "upload_router"
]