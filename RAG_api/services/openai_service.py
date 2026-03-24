"""
openai_service.py

Centralized OpenAI API client and service wrapper.
Handles LLM chat completions with consistent configuration and error handling.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.settings import settings

# Global OpenAI client instance
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create the global OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


class OpenAIService:
    """Centralized OpenAI service for LLM interactions."""
    
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or get_openai_client()
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate chat completion using OpenAI API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to settings.OPENAI_MODEL)
            temperature: Response randomness (0-2)
            max_tokens: Maximum response tokens
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=model or settings.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI API call failed: {e}")
            raise
    
    def generate_response(
        self, 
        system_prompt: str, 
        user_query: str,
        model: str = None,
        **kwargs
    ) -> str:
        """
        Generate response using system prompt and user query.
        
        Args:
            system_prompt: System/instruction prompt
            user_query: User's question or request
            model: Model name (defaults to settings.OPENAI_MODEL)
            **kwargs: Additional parameters for chat_completion
            
        Returns:
            Generated response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        return self.chat_completion(messages, model=model, **kwargs)
    
    def classify_text(
        self,
        text: str,
        categories: List[str],
        prompt_template: str = None,
        model: str = None
    ) -> str:
        """
        Classify text into one of the provided categories.
        
        Args:
            text: Text to classify
            categories: List of possible categories
            prompt_template: Custom classification prompt (optional)
            model: Model name (defaults to settings.OPENAI_MODEL)
            
        Returns:
            Selected category name
        """
        if prompt_template is None:
            categories_str = ' / '.join(categories)
            prompt_template = f"""
            Analyze the following text and classify it as: {categories_str}
            
            Text: "{text}"
            
            Respond with ONLY the category name, nothing else.
            """
        
        response = self.generate_response(
            system_prompt="You are a text classification assistant.",
            user_query=prompt_template,
            model=model,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        # Extract category from response
        response_clean = response.strip().upper()
        for category in categories:
            if category.upper() in response_clean:
                return category
        
        # Fallback to first category if none matched
        return categories[0]