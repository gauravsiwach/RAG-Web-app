"""
pdf_handler.py

PDF document chat handler using centralized services and core components.
Handles PDF-specific query processing, retrieval, and response generation.
"""

from typing import Tuple, Optional, Dict, Any
from config.settings import settings
from core import (
    translate_query,
    search_and_filter,
    guardrails_input,
    guardrails_output
)
from services import OpenAIService, get_openai_client


class PdfHandler:
    """Handler for PDF document queries."""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        """
        Initialize PDF handler with services.
        
        Args:
            openai_service: Optional OpenAI service instance
        """
        self.openai_service = openai_service or OpenAIService()
    
    def _generate_system_prompt(self, context: str) -> str:
        """
        Generate system prompt with PDF context.
        
        Args:
            context: Retrieved PDF context with page information
            
        Returns:
            Formatted system prompt
        """
        return f"""
You are a helpful AI Assistant who answers user queries based on the available context
retrieved from a PDF file along with page contents and page number.

You should only answer the user based on the following context and navigate the user
to open the right page number to know more.

Context:
{context}
"""
    
    def _build_context_from_results(self, search_results) -> str:
        """
        Build context string from search results with page information.
        
        Args:
            search_results: List of (document, score) tuples
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for doc, score in search_results:
            page_num = doc.metadata.get('page_label', 'Unknown')
            context_parts.append(
                f"Page Content: {doc.page_content}\nPage Number: {page_num}"
            )
        return "\n\n".join(context_parts)
    
    def _query_pdf_core(self, query: str) -> Tuple[str, str]:
        """
        Core PDF query logic without guardrails.
        
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
        search_results = search_and_filter(translated_queries, collection_suffix="pdf")

        # Early return if no relevant results found
        if not search_results:
            return (
                "Sorry, I couldn't find any relevant information for your query in this PDF. "
                "Please try asking something related to the document content.", 
                ""
            )

        # Step 3: Build context string from top unique results
        context = self._build_context_from_results(search_results)
        system_prompt = self._generate_system_prompt(context)

        print(f"\n📄 Context for LLM: {context}")

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
        Process PDF query with full pipeline including guardrails.
        
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
            answer, context = self._query_pdf_core(query)

            # If context is empty, this is a fallback (no LLM call made)
            if not context:
                return answer

            # OUTPUT guardrail — relevance check before returning
            final_answer = guardrails_output(query, answer, context)
            return final_answer

        except Exception as e:
            print(f"❌ Error in PDF handler: {e}")
            return "Sorry, there was an error processing your query. Please try again."


# Factory function for backward compatibility
def get_query_result_pdf(query: str) -> str:
    """
    Backward compatibility wrapper for PDF queries.
    
    Args:
        query: User query string
        
    Returns:
        Generated response
    """
    handler = PdfHandler()
    return handler.query(query)