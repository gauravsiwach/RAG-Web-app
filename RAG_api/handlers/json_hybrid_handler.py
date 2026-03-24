"""
json_hybrid_handler.py

JSON hybrid chat handler using centralized services and core components.
Pure Qdrant Hybrid Search Implementation for JSON Product Data (V2).
Uses Qdrant's native filtering capabilities instead of Pandas + Vector Search.
"""

import json
from typing import List, Dict, Any, Optional
from config.settings import settings
from core import (
    translate_query,
    classify_query_type,
    extract_structured_filters,
    guardrails_input,
    guardrails_output
)
from services import OpenAIService, QdrantService, EmbeddingService
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, SearchParams


def format_products_response(products: List[Dict], total_found: int, showing: int) -> str:
    """
    Convert structured product data to readable text format.
    
    Args:
        products: List of product dictionaries
        total_found: Total number of products found
        showing: Number of products being displayed
        
    Returns:
        str: Formatted response text
    """
    if not products:
        return "No products found matching your criteria."
    
    # Header
    response_lines = [f"Found {total_found} products" + (f", showing top {showing}:" if showing < total_found else ":"), ""]
    
    # Product list
    for i, product in enumerate(products, 1):
        price = f"₹{product.get('price', 0):.0f}"
        name = product.get('productName', 'Unknown')
        brand = product.get('brand', 'Unknown')
        category = product.get('categoryName', 'Unknown')
        
        # Format with promotions indicator
        promo_text = " 🏷️" if product.get('hasPromotions', False) else ""
        
        response_lines.append(f"{i}. **{name}** ({brand}) - {price}{promo_text}")
        response_lines.append(f"   Category: {category}")
        
        # Add taste description if available and relevant
        taste = product.get('taste', 'N/A')
        if taste and taste != 'N/A' and "N/A — not a food product" not in taste:
            response_lines.append(f"   Description: {taste}")
        
        response_lines.append("")  # Empty line between products
    
    return "\n".join(response_lines)


class JsonHybridHandler:
    """Handler for JSON product data queries using pure Qdrant hybrid search (V2)."""
    
    def __init__(
        self, 
        openai_service: Optional[OpenAIService] = None,
        qdrant_service: Optional[QdrantService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize JSON hybrid handler with services.
        
        Args:
            openai_service: Optional OpenAI service instance
            qdrant_service: Optional Qdrant service instance
            embedding_service: Optional Embedding service instance
        """
        self.openai_service = openai_service or OpenAIService()
        self.qdrant_service = qdrant_service or QdrantService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection_name = self.qdrant_service.get_collection_name("json")
    
    def _parse_hybrid_query(self, query: str) -> Dict[str, Any]:
        """
        Parse query into semantic and filter components using LLM extraction.
        
        Args:
            query: User query string
            
        Returns:
            Dict with semantic_query and filters
        """
        try:
            hybrid_parse_prompt = """
Parse this query into semantic and structured components for a hybrid search:

1. **semantic_part**: Extract descriptive/subjective terms that require similarity matching:
   - Taste qualities: "sweet", "crispy", "tangy", "refreshing", "spicy"
   - Quality descriptors: "good", "best", "popular", "premium"
   - Texture/experience: "smooth", "creamy", "fizzy", "bold"

2. **structured_filters**: Extract exact filterable criteria:
   - Price constraints: "under 50", "above 30", "between 20-40"
   - Brand names: "Coca-Cola", "Pepsi", "Amul", etc.
   - Categories: "Beverages", "Snacks", "Dairy", etc.
   - Promotions: "with discount", "on offer"

3. **handling_rules**:
   - If ONLY structured criteria → set semantic_part to null
   - If ONLY semantic terms → set structured_filters to {}
   - If mixed → extract both components

Return JSON:
{
  "semantic_query": "<descriptive terms or null>",
  "filters": {
    "price_lt": <number>,
    "price_gt": <number>, 
    "categoryName": "<category>",
    "brand": "<brand name>",
    "has_promotions": <boolean>,
    "search_term": "<product name search>"
  }
}

Examples:
"sweet snacks under 50" → {"semantic_query": "sweet snacks", "filters": {"price_lt": 50}}
"Coca-Cola products" → {"semantic_query": null, "filters": {"brand": "Coca-Cola"}}
"refreshing summer drinks" → {"semantic_query": "refreshing summer drinks", "filters": {}}
"list of water" → {"semantic_query": null, "filters": {"search_term": "water"}}

Respond ONLY with JSON. No explanations.
"""

            response = self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a query parsing assistant."},
                    {"role": "user", "content": f"{hybrid_parse_prompt}\n\nQuery to parse: '{query}'"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse JSON response
            parsed = json.loads(response)
            
            # Ensure required keys exist
            if "semantic_query" not in parsed:
                parsed["semantic_query"] = query
            if "filters" not in parsed:
                parsed["filters"] = {}
                
            return parsed
            
        except Exception as e:
            print(f"❌ Error parsing hybrid query: {e}")
            # Fallback: treat as pure semantic
            return {
                "semantic_query": query,
                "filters": {}
            }
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """
        Build Qdrant filter from extracted filter criteria.
        
        Args:
            filters: Dict of filter criteria
            
        Returns:
            Qdrant Filter object or None
        """
        try:
            conditions = []
            
            # Price filters
            if "price_lt" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.price",
                        range=Range(lt=filters["price_lt"])
                    )
                )
            
            if "price_gt" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.price", 
                        range=Range(gt=filters["price_gt"])
                    )
                )
            
            if "price_min" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.price",
                        range=Range(gte=filters["price_min"])
                    )
                )
            
            if "price_max" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.price",
                        range=Range(lte=filters["price_max"])
                    )
                )
            
            # Brand filter
            if "brand" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.brand",
                        match=MatchValue(value=filters["brand"])
                    )
                )
            
            # Category filter  
            if "categoryName" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.categoryName",
                        match=MatchValue(value=filters["categoryName"])
                    )
                )
            
            # Promotions filter
            if "has_promotions" in filters:
                conditions.append(
                    FieldCondition(
                        key="metadata.hasPromotions",
                        match=MatchValue(value=filters["has_promotions"])
                    )
                )
            
            if not conditions:
                return None
                
            return Filter(must=conditions)
            
        except Exception as e:
            print(f"❌ Error building Qdrant filter: {e}")
            return None
    
    def _hybrid_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Single-call Qdrant hybrid search with semantic + structured filtering.
        
        Args:
            query: User query string
            limit: Maximum number of results
            
        Returns:
            List of product dictionaries from Qdrant payload
        """
        print(f"\n🔀 Starting HYBRID search for: '{query}'")
        
        try:
            # Step 1: Parse query into semantic + filters
            parsed = self._parse_hybrid_query(query)
            semantic_query = parsed["semantic_query"]
            filters = parsed["filters"]
            
            print(f"🧠 Semantic component: {semantic_query}")
            print(f"🔧 Filter component: {filters}")

            # Step 2: Generate embedding for semantic part
            query_vector = None
            if semantic_query and str(semantic_query).strip():
                query_vector = self.embedding_service.embed_query(str(semantic_query))
            
            # Step 3: Build Qdrant filter for structured part
            qdrant_filter = self._build_qdrant_filter(filters)
            
            # Step 4: Execute hybrid search
            if query_vector:
                # Semantic + Structured (true hybrid)
                print("🔀 Executing semantic + filter hybrid search")
                results = self.qdrant_service.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                    score_threshold=0.1,  # Lower threshold for hybrid search
                    with_payload=True
                )
            elif qdrant_filter:
                # Only structured filters (no semantic)
                print("📊 Executing filter-only search")
                # Use a dummy query vector for filter-only search
                dummy_vector = [0.0] * self.embedding_service.get_embedding_dimension()
                results = self.qdrant_service.query_points(
                    collection_name=self.collection_name,
                    query=dummy_vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                    with_payload=True
                )
            else:
                # Fallback: basic semantic search
                print("🔍 Fallback to basic semantic search")
                if query_vector:
                    results = self.qdrant_service.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        limit=limit,
                        score_threshold=0.1,
                        with_payload=True
                    )
                else:
                    results = []
            
            # Step 5: Extract product data from payloads
            products = []
            for result in results:
                if "payload" in result and "metadata" in result["payload"]:
                    product_data = result["payload"]["metadata"]
                    product_data["_score"] = result.get("score", 0.0)
                    products.append(product_data)
            
            print(f"✅ Hybrid search found {len(products)} products")
            return products
            
        except Exception as e:
            print(f"❌ Error in hybrid search: {e}")
            return []
    
    def _handle_structured_query_v2(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Handle structured queries using Qdrant filtering.
        
        Args:
            query: Original query
            filters: Extracted filter criteria
            
        Returns:
            JSON response string
        """
        print(f"📊 Handling STRUCTURED query with Qdrant filters: {filters}")
        
        try:
            # Use hybrid search with no semantic component
            parsed_query = {
                "semantic_query": None,
                "filters": filters
            }
            
            # Build filter and execute search
            qdrant_filter = self._build_qdrant_filter(filters)
            if qdrant_filter:
                # Filter-only search
                dummy_vector = [0.0] * self.embedding_service.get_embedding_dimension()
                results = self.qdrant_service.query_points(
                    collection_name=self.collection_name,
                    query=dummy_vector,
                    query_filter=qdrant_filter,
                    limit=50,  # Higher limit for structured queries
                    with_payload=True
                )
                
                products = []
                for result in results:
                    if "payload" in result and "metadata" in result["payload"]:
                        products.append(result["payload"]["metadata"])
                
                # Format response
                if not products:
                    return json.dumps({
                        "summary": "No products found matching your criteria.",
                        "data": [],
                        "columns": []
                    })
                
                return json.dumps({
                    "summary": f"Found {len(products)} products matching your criteria, showing top {min(len(products), 10)}",
                    "data": products[:10],
                    "columns": ["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]
                })
            else:
                return json.dumps({
                    "summary": "No valid filters could be extracted from your query.",
                    "data": [],
                    "columns": []
                })
                
        except Exception as e:
            print(f"❌ Error in structured query: {e}")
            return json.dumps({"error": "Error processing structured query"})
    
    def _handle_semantic_query_v2(self, query: str) -> str:
        """
        Handle semantic queries using pure Qdrant vector search.
        
        Args:
            query: Original query
            
        Returns:
            JSON response string
        """
        print(f"🔍 Handling SEMANTIC query with pure Qdrant vector search")
        
        try:
            # Step 1: Translate query into multiple variants for better retrieval
            translated_queries = translate_query(query)
            print(f"🔄 Generated {len(translated_queries)} query variants")
            
            # Step 2: Create embeddings for all translated queries
            all_results = []
            for variant_query in translated_queries:
                query_embedding = self.embedding_service.embed_query(variant_query)
                if query_embedding:
                    # Search Qdrant with this variant
                    search_results = self.qdrant_service.query_points(
                        collection_name=self.collection_name,
                        query=query_embedding,
                        limit=15,  # Get top 15 per variant
                        score_threshold=0.1,  # Lower threshold for semantic search
                        with_payload=True
                    )
                    all_results.extend(search_results)
            
            # Step 3: Deduplicate and get top results
            seen_products = set()
            unique_products = []
            
            for result in all_results:
                if "payload" in result and "metadata" in result["payload"]:
                    product_data = result["payload"]["metadata"]
                    product_id = product_data.get("productId", product_data.get("productName", ""))
                    
                    if product_id and product_id not in seen_products:
                        product_data["_score"] = result.get("score", 0.0)
                        unique_products.append(product_data)
                        seen_products.add(product_id)
            
            # Step 4: Sort by relevance score and limit results
            unique_products.sort(key=lambda x: x.get("_score", 0.0), reverse=True)
            top_products = unique_products[:10]
            
            if not top_products:
                return json.dumps({
                    "summary": "Sorry, I couldn't find relevant products matching your description.",
                    "data": [],
                    "columns": []
                })
            
            # Step 5: Generate natural language response
            context = "\n".join([
                f"- {p.get('productName', 'Unknown')} by {p.get('brand', 'Unknown')} (₹{p.get('price', 'N/A')}) - {p.get('taste', 'No description')}"
                for p in top_products[:5]
            ])
            
            response_prompt = f"""
Based on these relevant products, provide a helpful recommendation response:

{context}

User Query: "{query}"

Respond with a JSON object containing your recommendations and explanations.
Format:
{{
    "summary": "Brief explanation of why these products match the user's request",
    "data": [
        {{"productName": "Product Name", "brand": "Brand", "price": "₹X", "categoryName": "Category", "reason": "Why this matches"}}
    ],
    "columns": ["productName", "brand", "price", "categoryName", "reason"]
}}
"""
            
            response = self.openai_service.generate_response(
                system_prompt="You are a helpful product recommendation assistant.",
                user_query=response_prompt,
                model=settings.OPENAI_MODEL
            )
            
            # Validate and return JSON response
            # Return the LLM response directly 
            return response
                
        except Exception as e:
            print(f"❌ Error in semantic query: {e}")
            return json.dumps({"error": "Error processing semantic query"})
    
    def _handle_hybrid_query_v2(self, query: str) -> str:
        """
        Handle hybrid queries using pure Qdrant hybrid search.
        
        Args:
            query: Original query
            
        Returns:
            JSON response string
        """
        print(f"🔀 Handling HYBRID query - Qdrant semantic + structured fusion")
        
        try:
            # Execute hybrid search
            products = self._hybrid_search(query, limit=10)
            
            if not products:
                return json.dumps({
                    "summary": "No products found matching your criteria.",
                    "data": [],
                    "columns": []
                })
            
            # Generate contextual response using LLM
            context = "\n".join([
                f"- {p.get('productName', 'Unknown')} by {p.get('brand', 'Unknown')} (₹{p.get('price', 'N/A')}) - {p.get('taste', 'No description')}"
                for p in products[:5]
            ])
            
            response_prompt = f"""
Based on these products found through hybrid search (combining semantic similarity and structured filters):

{context}

User Query: "{query}"

Provide a helpful response explaining why these products match both the descriptive and filtering aspects of the query.
Respond with JSON:
{{
    "summary": "Explanation of matches combining semantic similarity and filtering",
    "data": [{len(products)} products data],
    "columns": ["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]
}}
"""
            
            llm_response = self.openai_service.generate_response(
                system_prompt="You are a product search assistant specializing in hybrid queries.",
                user_query=response_prompt,
                model=settings.OPENAI_MODEL
            )
            
            # Return the LLM response directly
            return llm_response
                
        except Exception as e:
            print(f"❌ Error in hybrid query: {e}")
            return json.dumps({"error": "Error processing hybrid query"})
    
    def query(self, query: str) -> str:
        """
        Process JSON hybrid query with full pipeline including guardrails.
        
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
            
            # Step 2: Route to appropriate handler
            if query_type == "STRUCTURED":
                filters = extract_structured_filters(query)
                result = self._handle_structured_query_v2(query, filters)
            elif query_type == "HYBRID":
                result = self._handle_hybrid_query_v2(query)
            else:  # SEMANTIC (default)
                result = self._handle_semantic_query_v2(query)
            
            # Step 3: Apply OUTPUT guardrail
            context = f"Hybrid search result processed for {query_type} query"
            evaluated_response = guardrails_output(query, result, context)
            
            return evaluated_response
            
        except Exception as e:
            print(f"❌ Error in JSON hybrid handler: {e}")
            return "Sorry, there was an error processing your query. Please try again."


# Factory function for backward compatibility
def get_query_result_json_hybrid(query: str) -> str:
    """
    Backward compatibility wrapper for JSON hybrid queries.
    
    Args:
        query: User query string
        
    Returns:
        JSON response string
    """
    handler = JsonHybridHandler()
    return handler.query(query)