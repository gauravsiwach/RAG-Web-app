"""
Core RAG business logic package.

This package contains all shared RAG components used across different chat handlers:
- Query processing and classification
- Vector search operations
- Input/output validation (guardrails)
- Query translation and expansion
"""

from .guardrails import guardrails_input, guardrails_output
from .query_translation import translate_query
from .query_classifier import classify_query_type, extract_structured_filters
from .vector_search import search_and_filter, embedding_model

__all__ = [
    # Guardrails
    "guardrails_input", 
    "guardrails_output",
    # Query processing
    "translate_query",
    "classify_query_type", 
    "extract_structured_filters",
    # Vector search
    "search_and_filter",
    "embedding_model"
]