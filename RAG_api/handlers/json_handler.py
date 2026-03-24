"""
json_handler.py

JSON document chat handler using centralized services and core components.
Handles structured product data with V1 implementation (Pandas + Vector Search).
Supports STRUCTURED, SEMANTIC, and HYBRID query types.
"""

import os
import json
import pandas as pd
import re
from typing import Dict, Any, Optional, Union, List
from config.settings import settings
from core import (
    translate_query,
    search_and_filter,
    classify_query_type,
    extract_structured_filters,
    guardrails_input,
    guardrails_output
)
from services import OpenAIService


class JsonHandler:
    """Handler for JSON product data queries (V1 - Pandas + Vector Search)."""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        """
        Initialize JSON handler with services.
        
        Args:
            openai_service: Optional OpenAI service instance
        """
        self.openai_service = openai_service or OpenAIService()
    
    def _load_json_to_dataframe(self) -> pd.DataFrame:
        """
        Load JSON product data into a flattened pandas DataFrame.
        
        Returns:
            DataFrame with product data
        """
        try:
            # Path to the uploaded JSON file
            json_path = os.path.join(settings.UPLOAD_DIR, "product-data.json")
            
            if not os.path.exists(json_path):
                print(f"❌ JSON file not found at: {json_path}")
                return pd.DataFrame()
            
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Flatten the nested JSON structure
            products = []
            for category in data.get("categories", []):
                category_name = category.get("categoryName", "Unknown")
                category_id = category.get("categoryId", "")
                
                for product in category.get("products", []):
                    # Add category info to each product
                    product_flat = product.copy()
                    product_flat["categoryName"] = category_name
                    product_flat["categoryId"] = category_id
                    
                    # Flatten promotions for easier filtering
                    promotions = product.get("promotions", [])
                    if promotions:
                        product_flat["hasPromotions"] = True
                        product_flat["promotionTypes"] = [p.get("type", "") for p in promotions]
                    else:
                        product_flat["hasPromotions"] = False
                        product_flat["promotionTypes"] = []
                    
                    products.append(product_flat)
            
            df = pd.DataFrame(products)
            print(f"📊 Loaded {len(df)} products from JSON into DataFrame")
            return df
            
        except Exception as e:
            print(f"❌ Error loading JSON to DataFrame: {e}")
            return pd.DataFrame()
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any], query: str) -> pd.DataFrame:
        """
        Apply structured filters to the DataFrame.
        
        Args:
            df: Input DataFrame
            filters: Dict of filter criteria
            query: Original query for debugging
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        try:
            # Use LLM-extracted filters directly
            print(f"🔍 Applying LLM-extracted filters: {filters}")
            
            # Apply price filters
            if "price_min" in filters:
                filtered_df = filtered_df[filtered_df["price"] >= filters["price_min"]]
                print(f"💰 Applied price_min: ≥₹{filters['price_min']}")
                
            if "price_max" in filters:
                filtered_df = filtered_df[filtered_df["price"] <= filters["price_max"]]
                print(f"💰 Applied price_max: ≤₹{filters['price_max']}")
            
            # Apply brand filter
            if "brand" in filters:
                brand = filters["brand"]
                filtered_df = filtered_df[filtered_df["brand"].str.contains(brand, case=False, na=False)]
                print(f"🏷️ Applied brand filter: {brand}")
            
            # Apply category filter
            if "category" in filters:
                category = filters["category"]
                filtered_df = filtered_df[filtered_df["categoryName"].str.contains(category, case=False, na=False)]
                print(f"📂 Applied category filter: {category}")
            
            # Apply promotion filter
            if "has_promotions" in filters:
                if filters["has_promotions"]:
                    filtered_df = filtered_df[filtered_df["hasPromotions"] == True]
                    print("🎁 Applied filter: products with promotions only")
            
            # Apply search term filter for product names
            if "search_term" in filters:
                search_term = filters["search_term"]
                filtered_df = filtered_df[
                    filtered_df["productName"].str.contains(search_term, case=False, na=False) |
                    filtered_df["brand"].str.contains(search_term, case=False, na=False) |
                    filtered_df["taste"].str.contains(search_term, case=False, na=False)
                ]
                print(f"🔍 Applied search filter: '{search_term}'")
            
            print(f"✅ Filtering complete: {len(filtered_df)} products remaining")
            return filtered_df
            
        except Exception as e:
            print(f"❌ Error applying filters: {e}")
            return df
    
    def _handle_aggregation_query(self, query: str, df: pd.DataFrame, filtered_df: pd.DataFrame) -> str:
        """
        Handle aggregation queries (count, average, etc.).
        
        Args:
            query: Original query
            df: Original DataFrame  
            filtered_df: Filtered DataFrame
            
        Returns:
            JSON response string
        """
        try:
            query_lower = query.lower()
            
            # Aggregation patterns
            if any(word in query_lower for word in ["count", "how many", "number"]):
                count = len(filtered_df)
                
                if count == 0:
                    return json.dumps({
                        "summary": "No products found matching your criteria.",
                        "data": [],
                        "columns": []
                    }, indent=2)
                
                return json.dumps({
                    "summary": f"Found {count} products matching your criteria.",
                    "data": filtered_df[["productName", "brand", "price", "categoryName"]].head(5).to_dict('records'),
                    "columns": ["productName", "brand", "price", "categoryName"]
                }, indent=2)
            
            elif any(word in query_lower for word in ["average price", "mean price", "avg"]):
                if len(filtered_df) == 0:
                    return json.dumps({
                        "summary": "No products found to calculate average.",
                        "data": [],
                        "columns": []
                    }, indent=2)
                
                avg_price = filtered_df["price"].mean()
                return json.dumps({
                    "summary": f"Average price: ₹{avg_price:.2f} (from {len(filtered_df)} products)",
                    "data": [{"metric": "Average Price", "value": f"₹{avg_price:.2f}", "count": len(filtered_df)}],
                    "columns": ["metric", "value", "count"]
                }, indent=2)
            
            # Default: return top products  
            return json.dumps({
                "summary": f"Found {len(filtered_df)} products matching your criteria, showing top {min(len(filtered_df), 10)}",
                "data": filtered_df[["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]].head(10).to_dict('records'),
                "columns": ["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]
            }, indent=2)
            
        except Exception as e:
            print(f"❌ Error in aggregation query: {e}")
            return "Error processing aggregation query. Please try rephrasing your request."
    
    def _handle_structured_query(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Handle structured queries using DataFrame filtering.
        
        Args:
            query: Original query
            filters: Extracted filter criteria
            
        Returns:
            JSON response string
        """
        print(f"📊 Handling STRUCTURED query with filters: {filters}")
        
        try:
            # Load data
            df = self._load_json_to_dataframe()
            if df.empty:
                return "No product data available for processing your query."
            
            # Apply filters
            filtered_df = self._apply_filters(df, filters, query)
            
            # Handle aggregation or listing
            return self._handle_aggregation_query(query, df, filtered_df)
            
        except Exception as e:
            print(f"❌ Error in structured query: {e}")
            return "Error processing structured query. Please try rephrasing your request."
    
    def _handle_semantic_query(self, query: str) -> str:
        """
        Handle semantic queries using vector search.
        
        Args:
            query: Original query
            
        Returns:
            JSON response string
        """
        print(f"🔍 Handling SEMANTIC query with RAG pipeline")
        
        try:
            # Step 1: Translate query for better retrieval
            translated_queries = translate_query(query)
            
            # Step 2: Search vector store
            search_results = search_and_filter(translated_queries, collection_suffix="json")
            
            if not search_results:
                return "Sorry, I couldn't find relevant products matching your description."
            
            # Step 3: Build context from search results
            context_parts = []
            for doc, score in search_results:
                context_parts.append(f"Product: {doc.page_content}")
            context = "\n\n".join(context_parts)
            
            # Step 4: Generate response using OpenAI
            system_prompt = f"""
You are a helpful product recommendation assistant. Based on the following product information,
recommend products that match the user's request. Respond with a JSON object containing
your recommendations and explanations.

Product Information:
{context}

Format your response as:
{{
    "summary": "Brief explanation of matches", 
    "data": [
        {{"productName": "Product Name", "brand": "Brand", "price": 0, "categoryName": "Category", "reason": "Why this matches"}}
    ],
    "columns": ["productName", "brand", "price", "categoryName", "reason"]
}}
"""
            
            response = self.openai_service.generate_response(
                system_prompt=system_prompt,
                user_query=query,
                model=settings.OPENAI_MODEL
            )
            
            # Validate and return JSON response
            # Return the LLM response directly
            return response
                
        except Exception as e:
            print(f"❌ Error in semantic query: {e}")
            return "Error processing semantic query. Please try rephrasing your request."
    
    def _handle_hybrid_query(self, query: str) -> str:
        """
        Handle hybrid queries combining structured and semantic approaches.
        
        Args:
            query: Original query
            
        Returns:
            JSON response string
        """
        print(f"🔀 Handling HYBRID query - combining semantic and structured approaches")
        
        try:
            # Extract filters for structured part
            filters = extract_structured_filters(query)
            
            # Use semantic approach but could be enhanced to combine both
            return self._handle_semantic_query(query)
            
        except Exception as e:
            print(f"❌ Error in hybrid query: {e}")
            return "Error processing hybrid query. Please try rephrasing your request."
    
    def query(self, query: str) -> str:
        """
        Process JSON query with full pipeline including guardrails.
        
        Args:
            query: User query string
            
        Returns:
            JSON response string or error message
        """
        try:
            # INPUT guardrail — reject bad queries before any processing
            input_check = guardrails_input(query)
            if not input_check["passed"]:
                return input_check["message"]
                
            print(f"\n🧠 Original query: '{query}'")
            
            # Step 1: Classify query type
            query_type = classify_query_type(query)
            print(f"📂 Routing to handler for query type: {query_type}")
            
            # Step 2: Route to appropriate handler based on classification
            if query_type == "STRUCTURED":
                filters = extract_structured_filters(query)
                result = self._handle_structured_query(query, filters)
            elif query_type == "HYBRID":
                result = self._handle_hybrid_query(query)
            else:  # SEMANTIC (default)
                result = self._handle_semantic_query(query)
            
            # Step 3: Apply OUTPUT guardrail once (centralized)
            if isinstance(result, dict):
                response_str = json.dumps(result)
            else:
                response_str = result  # Already a JSON string
                
            context = "Query result processed through appropriate handler"
            evaluated_response = guardrails_output(query, response_str, context)
            
            # Return final response (guardrails handles JSON validation)
            return evaluated_response
            
        except Exception as e:
            print(f"❌ Error in JSON handler: {e}")
            return "Sorry, there was an error processing your query. Please try again."


# Factory function for backward compatibility
def get_query_result_json(query: str) -> str:
    """
    Backward compatibility wrapper for JSON queries.
    
    Args:
        query: User query string
        
    Returns:
        JSON response string
    """
    handler = JsonHandler()
    return handler.query(query)