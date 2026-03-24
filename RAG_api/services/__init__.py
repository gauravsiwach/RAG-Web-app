"""
services package

External service integrations and wrappers.
Provides centralized access to OpenAI API, Qdrant vector database, embedding services,
document indexing operations, and web crawling functionality.
"""

from .openai_service import OpenAIService, get_openai_client
from .qdrant_service import QdrantService, get_qdrant_client
from .embedding_service import EmbeddingService, get_embedding_model
from .indexing_service import (
    process_pdf_file,
    process_web_url_content, 
    process_json_file,
    # Legacy aliases for backward compatibility
    process_pdfFile
)
from .web_crawler_service import (
    crawl_webpage,
    crawl_all_pages,
    extract_text,
    extract_links,
    fetch_html
)

__all__ = [
    "OpenAIService",
    "get_openai_client",
    "QdrantService", 
    "get_qdrant_client",
    "EmbeddingService",
    "get_embedding_model",
    # Indexing functions
    "process_pdf_file",
    "process_web_url_content",
    "process_json_file",
    "process_pdfFile",  # Legacy alias
    # Web crawling functions
    "crawl_webpage",
    "crawl_all_pages",
    "extract_text",
    "extract_links",
    "fetch_html"
]