"""
web_url_handler.py

Web URL document chat handler using centralized services and core components.
Handles web page-specific query processing, retrieval, and response generation.
"""

from typing import Tuple, Optional, Dict, Any
from config.settings import settings
from core import (
    translate_query,
    search_and_filter,
    guardrails_input,
    guardrails_output
)
from services import OpenAIService


class WebUrlHandler:
    """Handler for web URL document queries."""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        """
        Initialize Web URL handler with services.
        
        Args:
            openai_service: Optional OpenAI service instance
        """
        self.openai_service = openai_service or OpenAIService()
    
    def _generate_system_prompt(self, context: str) -> str:
        """
        Generate system prompt with web page context.
        
        Args:
            context: Retrieved web page context
            
        Returns:
            Formatted system prompt
        """
        return f"""
You are a helpful AI Assistant who answers user queries based on the available context
retrieved from a web page.

You should only answer the user based on the following context.

Context:
{context}
"""
    
    def _build_context_from_results(self, search_results) -> str:
        """
        Build context string from search results.
        
        Args:
            search_results: List of (document, score) tuples
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for doc, score in search_results:
            context_parts.append(f"Page Content: {doc.page_content}")
        return "\n\n".join(context_parts)
    
    def _query_web_core(self, query: str) -> Tuple[str, str]:
        """
        Core web URL query logic without guardrails.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (answer, context)
        """
        print(f"\n🧠 Original query: '{query}'")

        # Step 1: Translate query into multiple variants for better retrieval
        translated_queries = translate_query(query)

        # Step 2: Search vector DB with all translated queries,
        # filter by relevance score, deduplicate, and rank results
        search_results = search_and_filter(translated_queries, collection_suffix="url")

        # Early return if no relevant results found
        if not search_results:
            return (
                "Sorry, I couldn't find any relevant information for your query in this web page. "
                "Try asking something related to the page content.", 
                ""
            )

        # Step 3: Build context string from top unique results
        context = self._build_context_from_results(search_results)
        system_prompt = self._generate_system_prompt(context)

        print(f"\n🌐 Context for LLM: {context}")

        # Step 4: Call OpenAI LLM with context + user query
        try:
            answer = self.openai_service.generate_response(
                system_prompt=system_prompt,
                user_query=query,
                model=settings.OPENAI_MODEL
            )
            
            print(f"\n🤖: {answer}")
            return (answer, context)
            
        except Exception as e:
            print(f"❌ Error in OpenAI call: {e}")
            return (
                "Sorry, there was an error generating a response. Please try again.", 
                context
            )
    
    def query(self, query: str) -> str:
        """
        Process web URL query with full pipeline including guardrails.
        
        Args:
            query: User query string
            
        Returns:
            Generated response or error message
        """
        try:
            # INPUT guardrail — reject bad queries before any LLM/vector calls
            input_check = guardrails_input(query)
            if not input_check["passed"]:
                return input_check["message"]

            # Core logic (returns answer, context)
            answer, context = self._query_web_core(query)

            # If context is empty, this is a fallback (no LLM call made)
            if not context:
                return answer

            # OUTPUT guardrail — relevance check before returning
            final_answer = guardrails_output(query, answer, context)
            return final_answer

        except Exception as e:
            print(f"❌ Error in Web URL handler: {e}")
            return "Sorry, there was an error processing your query. Please try again."


# Factory function for backward compatibility
def get_query_result_web(query: str) -> str:
    """
    Backward compatibility wrapper for web URL queries.
    
    Args:
        query: User query string
        
    Returns:
        Generated response
    """
    handler = WebUrlHandler()
    return handler.query(query)