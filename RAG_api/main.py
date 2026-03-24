"""
main.py

FastAPI application entry point with modular router organization.
Uses centralized config/, core/, services/, handlers/, and api/ packages.
"""

import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from api.endpoints import health_router, chat_router, upload_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    settings.validate()
    logger.info("✅ Configuration validation successful")
except Exception as e:
    logger.error(f"❌ Configuration validation failed: {e}")
    raise

# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description="""
    **Retrieval-Augmented Generation (RAG) Chatbot API**
    
    A comprehensive RAG system supporting multiple document types and query modes:
    
    ## Features
    
    ### 📄 **PDF Chat**
    - Upload and query PDF documents
    - Page-aware responses with navigation hints
    - Multi-query translation for better retrieval
    
    ### 🌐 **Web URL Chat**  
    - Crawl and query web page content
    - Async content extraction and processing
    - Web-optimized response generation
    
    ### 📊 **JSON Product Chat**
    - **V1**: Pandas-based structured + semantic search
    - **V2**: Pure Qdrant hybrid search with native filtering
    - Automatic query classification (STRUCTURED/SEMANTIC/HYBRID)
    - Natural language filter extraction
    
    ## RAG Pipeline
    - **Query Translation**: Multi-query expansion for better retrieval
    - **Vector Search**: Qdrant-powered similarity matching with relevance filtering  
    - **Guardrails**: Input validation and output relevance checking
    - **Hybrid Search**: Combines semantic similarity and structured filtering
    
    ## Technologies
    - **LLM**: OpenAI GPT-4o-mini
    - **Embeddings**: text-embedding-3-large  
    - **Vector DB**: Qdrant Cloud
    - **Framework**: FastAPI + Pydantic
    """,
    version="1.0.0",
    contact={
        "name": "RAG API Support",
        "email": "support@ragapi.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, tags=["Health"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(upload_router, tags=["Upload & Indexing"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("🚀 Starting RAG Chatbot API")
    logger.info(f"📋 Configuration: OpenAI Model = {settings.OPENAI_MODEL}")
    logger.info(f"📋 Configuration: Embedding Model = {settings.EMBEDDING_MODEL}")
    logger.info(f"📋 Configuration: Max File Size = {settings.MAX_FILE_SIZE // (1024*1024)}MB")
    logger.info(f"📋 Configuration: Relevance Threshold = {settings.RELEVANCE_THRESHOLD}")
    logger.info("✅ RAG API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("🛑 Shutting down RAG Chatbot API")
    logger.info("✅ Shutdown complete")


# Root endpoint
@app.get("/", include_in_schema=False)
def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0", 
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "PDF document chat",
            "Web URL chat",
            "JSON product data chat (V1 & V2)",
            "Multi-query translation",
            "Hybrid search", 
            "Guardrails & safety",
            "Vector similarity search"
        ]
    }


# Development server startup
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )

#uvicorn main:app --reload --host 0.0.0.0 --port 8000
