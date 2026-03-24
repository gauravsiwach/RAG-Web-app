"""
health.py

Health check and service status endpoints.
Provides monitoring and diagnostics information.
"""

from datetime import datetime
from fastapi import APIRouter
from ..models import HealthResponse
from config.settings import settings

router = APIRouter(
    prefix="",
    tags=["Health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the RAG API service is running and healthy."
)
def health_check():
    """
    Service health check endpoint.
    
    Returns:
        HealthResponse: Current service status and metadata
    """
    try:
        return HealthResponse(
            status="ok",
            message="RAG API is running",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        return HealthResponse(
            status="error", 
            message=f"Service health check failed: {str(e)}",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )


@router.get(
    "/status",
    response_model=dict,
    summary="Detailed Status",
    description="Get detailed service status including configuration and dependencies."
)
def detailed_status():
    """
    Detailed service status with configuration info.
    
    Returns:
        dict: Comprehensive service status information
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "service": "RAG API",
            "config": {
                "openai_model": settings.OPENAI_MODEL,
                "embedding_model": settings.EMBEDDING_MODEL,
                "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
                "relevance_threshold": settings.RELEVANCE_THRESHOLD
            },
            "features": {
                "pdf_chat": True,
                "web_url_chat": True, 
                "json_chat_v1": True,
                "json_chat_v2": True,
                "guardrails": True,
                "query_translation": True,
                "hybrid_search": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get detailed status: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }