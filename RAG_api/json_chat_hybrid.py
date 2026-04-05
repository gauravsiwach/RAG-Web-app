"""
json_chat_hybrid.py

Pure Qdrant Hybrid Search Implementation for JSON Product Data
Uses Qdrant's native filtering capabilities instead of Pandas + Vector Search

Key improvements:
- Single Qdrant search call with filters
- Better performance and scalability  
- True semantic + structured fusion
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, SearchParams
from langchain_openai import OpenAIEmbeddings

from query_translation import translate_query
from query_classifier import classify_query_type, extract_structured_filters
from response_judge import evaluate_and_filter_response
from guardrails import guardrails_input, guardrails_output
from language_translation import (
    detect_language,
    translate_to_english,
    translate_from_english
)

load_dotenv()

# Initialize clients
client = OpenAI()
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

# Qdrant configuration
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
collection_name = f"{os.getenv('QDRANT_COLLECTION')}_json"


def parse_hybrid_query(query: str) -> Dict[str, Any]:
    """
    Parse query into semantic and filter components using LLM extraction
    
    Returns:
    {
        "semantic_query": "sweet snacks",
        "filters": {"price_lt": 50, "categoryName": "Snacks"}
    }
    """
    try:
        HYBRID_PARSE_PROMPT = """
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": HYBRID_PARSE_PROMPT},
                {"role": "user", "content": f"Parse this query: {query}"},
            ],
            temperature=0.0,
            max_tokens=200
        )

        parsed = json.loads(response.choices[0].message.content)
        
        # Ensure required structure
        return {
            "semantic_query": parsed.get("semantic_query"),
            "filters": parsed.get("filters", {})
        }

    except Exception as e:
        print(f"❌ Error parsing hybrid query: {e}")
        # Fallback: treat as pure semantic
        return {"semantic_query": query, "filters": {}}


def build_qdrant_filter(filters: Dict[str, Any]) -> Optional[Filter]:
    """
    Build dynamic Qdrant filter from extracted filter criteria
    
    Args:
        filters: Dictionary with filter conditions
        
    Returns:
        Qdrant Filter object or None if no filters
    """
    conditions = []
    
    try:
        # Price range filters — stored under metadata.price in Qdrant
        if "price_lt" in filters:
            conditions.append(FieldCondition(
                key="metadata.price",
                range=Range(lt=filters["price_lt"])
            ))
            print(f"📍 Added price < {filters['price_lt']}")
        
        if "price_gt" in filters:
            conditions.append(FieldCondition(
                key="metadata.price", 
                range=Range(gt=filters["price_gt"])
            ))
            print(f"📍 Added price > {filters['price_gt']}")
        
        if "price_min" in filters:  # Alternative key name
            conditions.append(FieldCondition(
                key="metadata.price",
                range=Range(gte=filters["price_min"])
            ))
            print(f"📍 Added price >= {filters['price_min']}")
            
        if "price_max" in filters:  # Alternative key name
            conditions.append(FieldCondition(
                key="metadata.price",
                range=Range(lte=filters["price_max"])
            ))
            print(f"📍 Added price <= {filters['price_max']}")

        # Exact match filters — stored under metadata.* in Qdrant
        if "categoryName" in filters:
            conditions.append(FieldCondition(
                key="metadata.categoryName",
                match=MatchValue(value=filters["categoryName"])
            ))
            print(f"📍 Added category = {filters['categoryName']}")
            
        if "category" in filters:  # Alternative key name
            conditions.append(FieldCondition(
                key="metadata.categoryName", 
                match=MatchValue(value=filters["category"])
            ))
            print(f"📍 Added category = {filters['category']}")

        if "brand" in filters:
            conditions.append(FieldCondition(
                key="metadata.brand",
                match=MatchValue(value=filters["brand"])
            ))
            print(f"📍 Added brand = {filters['brand']}")

        if "has_promotions" in filters:
            conditions.append(FieldCondition(
                key="metadata.hasPromotions",
                match=MatchValue(value=filters["has_promotions"])
            ))
            print(f"📍 Added has_promotions = {filters['has_promotions']}")

        # Text search handling (for product name searches)
        if "search_term" in filters:
            # Note: Qdrant's text search would require full-text indexing
            # For now, we'll handle this at the application level
            print(f"📍 Search term '{filters['search_term']}' will be handled post-search")

        if conditions:
            filter_obj = Filter(must=conditions)
            print(f"🔧 Built Qdrant filter with {len(conditions)} conditions")
            return filter_obj
        else:
            print("🔧 No Qdrant filters to apply")
            return None

    except Exception as e:
        print(f"❌ Error building Qdrant filter: {e}")
        return None


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for semantic search using OpenAI"""
    try:
        if not text or not text.strip():
            return None
            
        # Use the same embedding model as indexing
        embedding = embedding_model.embed_query(text)
        print(f"🔗 Generated embedding for: '{text[:50]}...'")
        return embedding

    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None


def hybrid_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Single-call Qdrant hybrid search with semantic + structured filtering
    
    Args:
        query: User query string
        limit: Maximum number of results
        
    Returns:
        List of product dictionaries from Qdrant payload
    """
    print(f"\n🔀 Starting HYBRID search for: '{query}'")
    
    try:
        # Step 1: Parse query into semantic + filters
        parsed = parse_hybrid_query(query)
        semantic_query = parsed["semantic_query"]
        filters = parsed["filters"]
        
        print(f"🧠 Semantic component: {semantic_query}")
        print(f"🔧 Filter component: {filters}")

        # Step 2: Generate embedding for semantic part
        query_vector = None
        if semantic_query and semantic_query.strip():
            query_vector = generate_embedding(semantic_query)
        
        # Step 3: Build Qdrant filter for structured part
        qdrant_filter = build_qdrant_filter(filters)

        # Step 4: Handle edge cases
        if not query_vector and not qdrant_filter:
            print("⚠️ No semantic query or filters - returning empty results")
            return []

        # Step 5: Execute single Qdrant hybrid search
        search_params = SearchParams(
            hnsw_ef=128,  # Higher for better recall
            exact=False   # Approximate for speed
        )

        print(f"🔍 Executing Qdrant search (vector: {'Yes' if query_vector else 'No'}, filter: {'Yes' if qdrant_filter else 'No'})")
        
        search_results = qdrant_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=limit,
            with_payload=True,
            search_params=search_params
        ).points

        # Step 6: Extract and process results
        # LangChain stores structured fields under payload["metadata"]
        results = []
        for hit in search_results:
            meta = hit.payload.get("metadata", hit.payload)
            meta["_score"] = hit.score
            meta["page_content"] = hit.payload.get("page_content", "")
            results.append(meta)
            
        print(f"✅ Hybrid search returned {len(results)} results")
        
        # Step 7: Handle search_term filtering (post-processing)
        if "search_term" in filters and results:
            search_term = filters["search_term"].lower()
            filtered_results = []
            
            for result in results:
                product_text = (
                    result.get("productName", "").lower() + " " +
                    result.get("brand", "").lower() + " " +
                    result.get("taste", "").lower()
                )
                
                if search_term in product_text:
                    filtered_results.append(result)
                    
            results = filtered_results
            print(f"🔍 After search term filtering: {len(results)} results")

        return results

    except Exception as e:
        print(f"❌ Error in hybrid search: {e}")
        return []


def handle_hybrid_query_v2(query: str) -> str:
    """
    Handle hybrid queries using pure Qdrant search (V2 implementation)
    
    Returns JSON response string
    """
    print(f"\n🔀 Handling HYBRID query (V2): {query}")
    
    try:
        # Execute hybrid search
        search_results = hybrid_search(query, limit=5)
        
        if not search_results:
            return json.dumps({
                "summary": "No products found matching your criteria.",
                "data": [],
                "columns": []
            })

        # Format response - extract relevant fields for display  
        display_columns = ["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]
        formatted_results = []
        
        for result in search_results:
            # Extract only display columns that exist
            display_result = {}
            for col in display_columns:
                if col in result:
                    display_result[col] = result[col]
            formatted_results.append(display_result)

        # Generate summary
        count = len(formatted_results)
        if count > 0:
            min_price = min(r["price"] for r in formatted_results)
            max_price = max(r["price"] for r in formatted_results) 
            price_range = f"₹{min_price} - ₹{max_price}" if count > 1 else f"₹{min_price}"
            summary = f"Found {count} products matching your criteria. Price range: {price_range}."
        else:
            summary = "No products found."

        response = {
            "summary": summary,
            "data": formatted_results,
            "columns": [col for col in display_columns if any(col in r for r in formatted_results)]
        }

        # Apply response evaluation
        response_str = json.dumps(response)
        evaluated_response = evaluate_and_filter_response(query, response_str, 
                                                         json.dumps(search_results))
        
        print(f"✅ Hybrid query V2 completed successfully")
        return evaluated_response

    except Exception as e:
        print(f"❌ Error in hybrid query V2: {e}")
        return json.dumps({
            "summary": f"Error processing hybrid query: {str(e)}",
            "data": [],
            "columns": []
        })


def get_query_result_json_hybrid(query: str) -> str:
    """
    Main entry point for hybrid JSON chat (V2 implementation)
    
    Routes queries to appropriate handlers based on classification:
    - STRUCTURED: Direct Qdrant filtering (pure structured search)
    - SEMANTIC: Pure Qdrant vector search
    - HYBRID: Qdrant hybrid search with semantic + filters
    """
    import time
    try:
        step_times = {}
        start_total = time.time()

        # Step 1: Detect language and translate to English if needed
        start = time.time()
        detected_lang = detect_language(query)
        print(f"🌍 Detected language: {detected_lang}")
        step_times['detect_language'] = time.time() - start

        start = time.time()
        if detected_lang != "en":
            english_query, _ = translate_to_english(query, detected_lang)
            original_lang = detected_lang
        else:
            english_query = query
            original_lang = "en"
        step_times['translate_to_english'] = time.time() - start

        # Step 2: INPUT guardrail — reject bad queries before any processing
        start = time.time()
        input_check = guardrails_input(english_query)
        step_times['guardrails_input'] = time.time() - start
        if not input_check["passed"]:
            error_msg = input_check["message"]
            # Translate error back if needed
            start = time.time()
            if original_lang != "en":
                error_msg = translate_from_english(error_msg, original_lang)
            step_times['translate_error'] = time.time() - start
            print(f"⏱️ Step times: {step_times}")
            return error_msg

        print(f"\n🧠 Hybrid V2 query: '{english_query}'")

        # Step 3: Classify query type using the same logic as original
        start = time.time()
        query_type = classify_query_type(english_query)
        step_times['classify_query_type'] = time.time() - start
        print(f"📂 Routing to handler for query type: {query_type}")

        # Step 4: Route to appropriate handler based on classification
        start = time.time()
        if query_type == "STRUCTURED":
            filters = extract_structured_filters(english_query)
            result = handle_structured_query_v2(english_query, filters)
        elif query_type == "SEMANTIC":
            result = handle_semantic_query_v2(english_query)
        else:  # HYBRID (default)
            result = handle_hybrid_query_v2(english_query)
        step_times['vector search handler'] = time.time() - start

        # Step 5: Apply OUTPUT guardrail once (centralized)
        start = time.time()
        context = "Hybrid query result processed through appropriate handler"
        evaluated_response = guardrails_output(english_query, result, context)
        step_times['guardrails_output'] = time.time() - start

        # Step 6: Translate response back to original language if needed
        start = time.time()
        if original_lang != "en":
            evaluated_response = translate_from_english(evaluated_response, original_lang)
        step_times['translate_from_english'] = time.time() - start

        print(f"\n🤖 Hybrid V2 result ready: {query_type}")
        step_times['total'] = time.time() - start_total
        print(f"⏱️ Step times: {step_times}")
        return evaluated_response

    except Exception as e:
        print(f"❌ Error in hybrid JSON chat: {e}")
        return json.dumps({
            "summary": "Sorry, there was an error processing your query. Please try again.",
            "data": [],
            "columns": []
        })


def handle_structured_query_v2(query: str, filters: dict) -> str:
    """
    Handle structured queries using pure Qdrant filtering (no vector search)
    
    For queries that need exact filtering: price ranges, categories, brands, etc.
    Uses only Qdrant's filter capabilities without semantic embeddings.
    """
    print(f"📈 Handling STRUCTURED query with pure Qdrant filters: {filters}")
    
    try:
        # Build Qdrant filter from extracted filters
        qdrant_filter = build_qdrant_filter(filters)
        
        if not qdrant_filter:
            # No valid filters - return error
            return json.dumps({
                "summary": "No valid filters could be extracted from your query for structured search.",
                "data": [],
                "columns": []
            })
        
        # Use a dummy query vector for structured-only search
        # We'll get ALL matching documents based on filters alone
        dummy_vector = [0.0] * 3072  # text-embedding-3-large dimension
        
        search_results = qdrant_client.query_points(
            collection_name=collection_name,
            query=dummy_vector,
            query_filter=qdrant_filter,
            limit=50,  # Get more results for structured queries
            with_payload=True,
            search_params=SearchParams(exact=True)  # Don't use approximate search for structured
        ).points
        
        if not search_results:
            return json.dumps({
                "summary": "No products found matching your filter criteria.",
                "data": [],
                "columns": []
            })
        
        # Format structured results — metadata stored under payload["metadata"]
        products = []
        for result in search_results:
            meta = result.payload.get("metadata", result.payload)
            products.append({
                "productName": meta.get("productName", ""),
                "brand": meta.get("brand", ""),
                "price": meta.get("price", 0),
                "categoryName": meta.get("categoryName", ""),
                "taste": meta.get("taste", "N/A"),
                "hasPromotions": meta.get("hasPromotions", False)
            })
        
        # Create summary
        count = len(products)
        prices = [p["price"] for p in products if p["price"]]
        price_range = f"₹{min(prices)} - ₹{max(prices)}" if len(prices) > 1 else f"₹{prices[0]}" if prices else "N/A"
        
        summary = f"Found {count} products matching your filter criteria. Price range: {price_range}."
        
        structured_response = {
            "summary": summary,
            "data": products,
            "columns": ["productName", "brand", "price", "categoryName", "taste", "hasPromotions"]
        }
        
        # Evaluate response quality
        response_str = json.dumps(structured_response)
        context = f"Structured search results: {len(products)} products found"
        evaluated_response = evaluate_and_filter_response(query, response_str, context)
        
        return evaluated_response if isinstance(evaluated_response, str) else json.dumps(evaluated_response)
        
    except Exception as e:
        print(f"❌ Error in structured query v2: {e}")
        return json.dumps({
            "summary": f"Error processing structured query: {str(e)}",
            "data": [],
            "columns": []
        })


def handle_semantic_query_v2(query: str) -> str:
    """
    Handle semantic queries using pure Qdrant vector search (no filtering)
    
    For queries that need similarity/RAG: taste descriptions, recommendations, etc.
    Uses only semantic embeddings without structured filters.
    """
    print(f"🔍 Handling SEMANTIC query with pure Qdrant vector search")
    
    try:
        # Step 1: Translate query into multiple variants for better retrieval
        translated_queries = translate_query(query)
        print(f"🔄 Generated {len(translated_queries)} query variants")
        
        # Step 2: Create embeddings for all translated queries
        all_results = []
        for variant_query in translated_queries:
            query_embedding = embedding_model.embed_query(variant_query)
            
            # Search Qdrant with this variant
            search_results = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=15,  # Get top 15 per variant
                with_payload=True,
                score_threshold=0.1  # Lower threshold for semantic search
            ).points
            # print search results for debugging
            print(f"\n🔍 Search results for variant '{variant_query}': '{len(search_results)}'")
                  
            # Add query variant info to results
            for result in search_results:
                all_results.append({
                    'result': result,
                    'query_variant': variant_query,
                    'score': result.score
                })
        
        if not all_results:
            return json.dumps({
                "summary": "Sorry, I couldn't find any relevant information for your query.",
                "data": [],
                "columns": []
            })
        
        # Step 3: Sort by score and remove duplicates
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        seen_products = set()
        unique_results = []
        for item in all_results:
            product_id = item['result'].payload.get('productId', item['result'].payload.get('id', str(item['result'].id)))
            if product_id not in seen_products:
                unique_results.append(item)
                seen_products.add(product_id)
        
        # Take top 5 unique results for LLM context to avoid timeouts
        top_results = unique_results[:3]

        # Debug: serialize only the payload (ScoredPoint is not JSON serializable)
        # debug_data = [{'score': item['score'], 'payload': item['result'].payload} for item in top_results]
        # json_str = json.dumps(debug_data, default=str)
        # print(f"✅ Top {len(top_results)} results, JSON size: {len(json_str)} chars")
        # print(f"📦 Top results content: {json_str[:500]}...")

        # Step 4: Build context from page_content (LangChain stores text there)
        context_parts = []
        for item in top_results:
            payload = item['result'].payload
            page_content = payload.get('page_content', '')
            if page_content:
                context_parts.append(page_content)

        combined_context = "\n\n".join(context_parts)

        # print the length of the combined context for debugging
        print(f"📚 Combined LLM context length: {len(combined_context)}")

        # Step 5: Generate semantic response with LLM
        response = generate_semantic_response(query, combined_context)

        print(f"✅ Generated semantic response from LLM for combined context: '{combined_context}'")
        print(f"🤖 Semantic response: {response}")

        # Step 6: Evaluate response relevance
        evaluated_response = evaluate_and_filter_response(query, response, combined_context)

        return evaluated_response if isinstance(evaluated_response, str) else json.dumps(evaluated_response)
        
    except Exception as e:
        print(f"❌ Error in semantic query v2: {e}")
        return json.dumps({
            "summary": f"Error processing semantic query: {str(e)}",
            "data": [],
            "columns": []
        })


def generate_semantic_response(query: str, context: str) -> str:
    """
    Generate structured JSON response using LLM for semantic queries
    """
    SEMANTIC_SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant who answers user queries based on the available context
    retrieved from a JSON product data file using semantic search.

    You MUST respond ONLY with a valid JSON object in the following format:
    {{
      "summary": "<one or two sentence answer to the user query>",
      "data": [
        {{ "<field>": "<value>", ... }},
        ...
      ],
      "columns": ["<field1>", "<field2>", ...]
    }}

    Rules:
    - "summary": always include a plain-language answer addressing the user's semantic intent.
    - "data": include the matching product records as an array of objects. If no tabular data is relevant, set to [].
    - "columns": list the keys used in the data rows (same order). If data is [], set to [].
    - Answer ONLY from the context below. Do not invent values.
    - Focus on semantic relevance: taste, quality, recommendations based on user intent.
    - Do NOT wrap the JSON in markdown code fences.

    Context:
    {context}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SEMANTIC_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.2  # Slight creativity for semantic interpretation
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating semantic response: {e}")
        return json.dumps({
            "summary": "Error generating response from semantic search results.",
            "data": [],
            "columns": []
        })
