"""
chat.py

Chat endpoints for different document types.
Handles PDF, web URL, and JSON queries with comprehensive RAG pipeline.
"""

from fastapi import APIRouter, HTTPException, status
from ..models import ChatRequest, ChatResponse, ErrorResponse
from handlers import (
    get_query_result_pdf,
    get_query_result_web,
    get_query_result_json,
    get_query_result_json_hybrid
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["Chat"],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "/pdf_chat",
    response_model=ChatResponse,
    summary="PDF Document Chat", 
    description="Query uploaded PDF documents using RAG with query translation and guardrails."
)
def pdf_chat_endpoint(request: ChatRequest):
    """
    Process queries against uploaded PDF documents.
    
    Features:
    - Multi-query translation for better retrieval
    - Vector similarity search with relevance filtering  
    - Page-aware response with navigation hints
    - Input/output guardrails for safety
    
    Args:
        request: Chat request with user message
        
    Returns:
        ChatResponse: Generated answer based on PDF content
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"PDF chat request: {request.message[:100]}...")
        
        # Delegate to PDF handler
        result = get_query_result_pdf(request.message)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response for PDF query"
            )
        
        logger.info("PDF chat response generated successfully")
        return ChatResponse(reply=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PDF chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF chat processing failed: {str(e)}"
        )


@router.post(
    "/web_url_chat", 
    response_model=ChatResponse,
    summary="Web URL Chat",
    description="Query processed web pages using RAG with content-aware responses."
)
def web_url_chat_endpoint(request: ChatRequest):
    """
    Process queries against crawled web page content.
    
    Features:
    - Multi-query translation for better retrieval
    - Vector similarity search across web content
    - Web-optimized system prompts
    - Input/output guardrails for safety
    
    Args:
        request: Chat request with user message
        
    Returns:
        ChatResponse: Generated answer based on web content
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Web URL chat request: {request.message[:100]}...")
        
        # Delegate to web URL handler
        result = get_query_result_web(request.message)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response for web URL query"
            )
        
        logger.info("Web URL chat response generated successfully")
        return ChatResponse(reply=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Web URL chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Web URL chat processing failed: {str(e)}"
        )


@router.post(
    "/json_chat",
    response_model=ChatResponse,
    summary="JSON Product Data Chat",
    description="Query structured product data with automatic query classification and hybrid search."
)
def json_chat_endpoint(request: ChatRequest):
    """
    Process queries against structured JSON product data.
    
    Features:
    - Automatic query classification (STRUCTURED/SEMANTIC/HYBRID)
    - V1: Pandas-based filtering + vector search
    - V2: Pure Qdrant hybrid search with native filtering
    - Natural language filter extraction
    - Aggregation support (count, average, etc.)
    - Input/output guardrails for safety
    
    Args:
        request: Chat request with message and version selection
        
    Returns:
        ChatResponse: JSON response with product data and analysis
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"JSON chat request (v{request.version}): {request.message[:100]}...")
        
        # Route to appropriate handler based on version
        if request.version == "v1":
            logger.info("Using V1 handler: Pandas + Vector Search")
            result = get_query_result_json(request.message)
        else:  # v2 (default)
            logger.info("Using V2 handler: Pure Qdrant Hybrid Search")
            result = get_query_result_json_hybrid(request.message)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response for JSON query"
            )
        
        logger.info("JSON chat response generated successfully")
        return ChatResponse(reply=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in JSON chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JSON chat processing failed: {str(e)}"
        )


# Additional utility endpoints for chat functionality
@router.get(
    "/chat/capabilities",
    summary="Chat Capabilities",
    description="Get information about supported chat modes and features."
)
def get_chat_capabilities():
    """
    Get information about available chat capabilities.
    
    Returns:
        dict: Detailed capabilities and feature support
    """
    return {
        "pdf_chat": {
            "description": "Query uploaded PDF documents",
            "features": ["multi_query_translation", "page_navigation", "guardrails"],
            "supported_formats": [".pdf"]
        },
        "web_url_chat": {
            "description": "Query crawled web pages", 
            "features": ["multi_query_translation", "content_extraction", "guardrails"],
            "supported_protocols": ["http", "https"]
        },
        "json_chat": {
            "description": "Query structured product data",
            "versions": {
                "v1": "Pandas + Vector Search",
                "v2": "Pure Qdrant Hybrid Search"
            },
            "features": ["query_classification", "natural_language_filters", "aggregations", "hybrid_search"],
            "query_types": ["STRUCTURED", "SEMANTIC", "HYBRID"]
        },
        "common_features": ["input_guardrails", "output_guardrails", "relevance_filtering", "error_handling"]
    }