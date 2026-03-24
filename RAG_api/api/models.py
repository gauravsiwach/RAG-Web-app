"""
models.py

Pydantic models for FastAPI request/response validation.
Centralizes all API model definitions for consistent validation and documentation.
"""

from pydantic import BaseModel, HttpUrl, validator, Field
from typing import Optional, Dict, Any, Union, List
from enum import Enum


class ChatVersion(str, Enum):
    """JSON chat engine version selection."""
    V1 = "v1"  # Pandas + Vector Search  
    V2 = "v2"  # Pure Qdrant Hybrid Search


class ChatRequest(BaseModel):
    """Request model for chat endpoints."""
    
    message: str = Field(
        ..., 
        min_length=1,
        max_length=2000,
        description="User query message",
        example="What is React component composition?"
    )
    version: ChatVersion = Field(
        default=ChatVersion.V2,
        description="Chat engine version for JSON queries"
    )
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoints."""
    
    reply: str = Field(
        ...,
        description="Generated response from RAG system",
        example="React component composition allows you to combine components..."
    )


class UploadResponse(BaseModel):
    """Response model for file upload endpoints."""
    
    filename: str = Field(..., description="Name of uploaded file")
    size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Upload status message")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "document.pdf",
                "size": 1024567,
                "message": "File uploaded successfully and indexing is done."
            }
        }


class UrlRequest(BaseModel):
    """Request model for web URL processing."""
    
    url: HttpUrl = Field(
        ...,
        description="Web page URL to process",
        example="https://react.dev/learn"
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message") 
    version: Optional[str] = Field(None, description="API version")
    timestamp: Optional[str] = Field(None, description="Current timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "message": "RAG API is running", 
                "version": "1.0.0",
                "timestamp": "2026-03-24T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Internal error code")
    timestamp: Optional[str] = Field(None, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "File processing failed",
                "error_code": "PROCESSING_ERROR",
                "timestamp": "2026-03-24T10:30:00Z"
            }
        }


# JSON Response Models for structured data
class StructuredResponse(BaseModel):
    """Response model for structured JSON queries."""
    
    type: str = Field(..., description="Response type")
    total_found: int = Field(..., description="Total matching products") 
    showing: int = Field(..., description="Number of products shown")
    products: List[Dict[str, Any]] = Field(..., description="Product list")


class SemanticResponse(BaseModel):
    """Response model for semantic JSON queries."""
    
    type: str = Field(..., description="Response type") 
    recommendations: List[Dict[str, str]] = Field(..., description="Product recommendations")
    summary: str = Field(..., description="Explanation summary")


class HybridResponse(BaseModel):
    """Response model for hybrid JSON queries."""
    
    type: str = Field(..., description="Response type")
    summary: str = Field(..., description="Search explanation")
    total_found: int = Field(..., description="Total matching products")
    products: List[Dict[str, Any]] = Field(..., description="Product list")


# Union type for JSON responses
JsonChatResponse = Union[StructuredResponse, SemanticResponse, HybridResponse, Dict[str, Any]]