"""
handlers package

Domain-specific chat handlers that orchestrate core/ and services/ components.
Each handler focuses on a specific document type (PDF, Web URL, JSON) and implements
the complete RAG pipeline from query processing to response generation.
"""

from .pdf_handler import PdfHandler, get_query_result_pdf
from .web_url_handler import WebUrlHandler, get_query_result_web  
from .json_handler import JsonHandler, get_query_result_json
from .json_hybrid_handler import JsonHybridHandler, get_query_result_json_hybrid

__all__ = [
    "PdfHandler",
    "get_query_result_pdf", 
    "WebUrlHandler",
    "get_query_result_web",
    "JsonHandler", 
    "get_query_result_json",
    "JsonHybridHandler",
    "get_query_result_json_hybrid"
]