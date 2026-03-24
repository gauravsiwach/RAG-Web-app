import os
import json
import pandas as pd
import re
from dotenv import load_dotenv
from openai import OpenAI
from query_translation import translate_query
from vector_search import search_and_filter
from query_classifier import classify_query_type, extract_structured_filters
from response_judge import evaluate_and_filter_response
from guardrails import guardrails_input, guardrails_output

load_dotenv()

client = OpenAI()


def load_json_to_dataframe():
    """
    Load JSON product data into a flattened pandas DataFrame
    """
    try:
        # Path to the uploaded JSON file
        json_path = os.path.join("uploaded_files", "product-data.json")
        
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


def apply_filters(df, filters, query):
    """
    Apply structured filters to the DataFrame
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


def extract_enhanced_filters(query, base_filters):
    """
    Enhanced filter extraction from query text using regex patterns
    """
    filters = base_filters.copy() if base_filters else {}
    query_lower = query.lower()
    
    # Price range patterns  
    price_patterns = [
        (r"under[\s₹]*([0-9]+)", "price_max"),
        (r"below[\s₹]*([0-9]+)", "price_max"), 
        (r"less than[\s₹]*([0-9]+)", "price_max"),
        (r"<[\s₹]*([0-9]+)", "price_max"),
        (r"above[\s₹]*([0-9]+)", "price_min"),
        (r"over[\s₹]*([0-9]+)", "price_min"),
        (r"more than[\s₹]*([0-9]+)", "price_min"),
        (r">[\s₹]*([0-9]+)", "price_min"),
        (r"between[\s₹]*([0-9]+)[\s-and₹]*([0-9]+)", "price_range"),
    ]
    
    for pattern, filter_type in price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if filter_type == "price_range":
                filters["price_min"] = int(match.group(1))
                filters["price_max"] = int(match.group(2))
            else:
                filters[filter_type] = int(match.group(1))
            break
    
    # Brand patterns - improved mapping
    brands = ["coca-cola", "pepsi", "sprite", "fanta", "nestlé", "nestle", "amul", "lay's", "lays", 
              "kurkure", "doritos", "haldiram", "pringles", "bingo", "too yumm", "real", "tropicana",
              "britannia", "kwality walls", "yakult", "epigamia", "red bull"]
    for brand in brands:
        if brand in query_lower:
            # Improved brand name normalization
            if brand == "nestlé" or brand == "nestle":
                filters["brand"] = "Nestle"
            elif brand == "lay's" or brand == "lays":
                filters["brand"] = "Lay's"
            elif brand == "too yumm":
                filters["brand"] = "Too Yumm"
            elif brand == "kwality walls":
                filters["brand"] = "Kwality Walls"
            elif brand == "red bull":
                filters["brand"] = "Red Bull"
            else:
                filters["brand"] = brand.title().replace(" ", " ")
            break
    
    # Category patterns
    categories = ["beverages", "snacks", "dairy", "personal care", "household", "drinks", "chips"]
    for category in categories:
        if category in query_lower:
            # Map common terms to actual categories
            if category in ["drinks"]:
                filters["category"] = "Beverages"
            elif category in ["chips"]:
                filters["category"] = "Snacks"
            else:
                filters["category"] = category.title()
            break
    
    # Promotion patterns
    if any(word in query_lower for word in ["promotion", "discount", "offer", "deal"]):
        filters["has_promotions"] = True
    
    return filters


def is_aggregation_query(query):
    """
    Check if the query requires aggregation (count, sum, average)
    """
    aggregation_keywords = [
        "how many", "count", "total", "number of", "sum", "average", "avg", 
        "mean", "cheapest", "most expensive", "lowest", "highest"
    ]
    return any(keyword in query.lower() for keyword in aggregation_keywords)


def handle_aggregation_query(query, df, filtered_df):
    """
    Handle queries that require aggregation operations
    """
    query_lower = query.lower()
    
    # Count queries
    if any(word in query_lower for word in ["how many", "count", "total", "number of"]):
        count = len(filtered_df)
        return {
            "summary": f"Found {count} products matching your criteria.",
            "data": [{"count": count}],
            "columns": ["count"]
        }
    
    # Price aggregations
    if "average" in query_lower or "avg" in query_lower or "mean" in query_lower:
        avg_price = filtered_df["price"].mean() if len(filtered_df) > 0 else 0
        return {
            "summary": f"Average price of matching products is ₹{avg_price:.2f}.",
            "data": [{"average_price": round(avg_price, 2), "product_count": len(filtered_df)}],
            "columns": ["average_price", "product_count"]
        }
    
    # Min/Max price queries
    if "cheapest" in query_lower or "lowest" in query_lower:
        if len(filtered_df) > 0:
            cheapest = filtered_df.loc[filtered_df["price"].idxmin()]
            return {
                "summary": f"Cheapest product: {cheapest['productName']} at ₹{cheapest['price']}",
                "data": [cheapest.to_dict()],
                "columns": list(cheapest.index)
            }
        else:
            return {
                "summary": "No products found matching your criteria.",
                "data": [],
                "columns": []
            }
    
    if "most expensive" in query_lower or "highest" in query_lower:
        if len(filtered_df) > 0:
            most_expensive = filtered_df.loc[filtered_df["price"].idxmax()]
            return {
                "summary": f"Most expensive product: {most_expensive['productName']} at ₹{most_expensive['price']}",
                "data": [most_expensive.to_dict()],
                "columns": list(most_expensive.index)
            }
        else:
            return {
                "summary": "No products found matching your criteria.",
                "data": [],
                "columns": []
            }
    
    # Default: return filtered results
    return format_structured_response(query, filtered_df)


def apply_sorting(df, query):
    """
    Apply sorting to the DataFrame based on query keywords
    """
    if df.empty:
        return df
    
    query_lower = query.lower()
    
    # Price sorting
    if "cheapest" in query_lower or "lowest price" in query_lower:
        return df.sort_values("price", ascending=True)
    elif "most expensive" in query_lower or "highest price" in query_lower:
        return df.sort_values("price", ascending=False)
    
    # Name sorting
    if "alphabetical" in query_lower or "a to z" in query_lower:
        return df.sort_values("productName", ascending=True)
    
    # Default: sort by price (ascending)
    return df.sort_values("price", ascending=True)


def format_structured_response(query, df):
    """
    Format the filtered DataFrame into the expected response structure
    """
    if df.empty:
        return {
            "summary": "No products found matching your criteria.",
            "data": [],
            "columns": []
        }
    
    # Select relevant columns for display
    display_columns = ["productName", "brand", "price", "categoryName"]
    if "taste" in df.columns:
        display_columns.append("taste")
    if "hasPromotions" in df.columns:
        display_columns.append("hasPromotions")
    
    # Filter to existing columns
    available_columns = [col for col in display_columns if col in df.columns]
    display_df = df[available_columns]
    
    # Convert to records
    data_records = display_df.to_dict('records')
    
    # Create summary
    count = len(df)
    price_range = f"₹{df['price'].min()} - ₹{df['price'].max()}" if count > 1 else f"₹{df['price'].iloc[0]}"
    
    summary = f"Found {count} products matching your criteria. Price range: {price_range}."
    
    return {
        "summary": summary,
        "data": data_records,
        "columns": available_columns
    }


def handle_structured_query(query, filters):
    """
    Handle structured/database-style queries using pandas for direct JSON operations
    """
    print(f"📊 Handling STRUCTURED query with filters: {filters}")
    
    try:
        # Step 1: Load JSON data into pandas DataFrame
        df = load_json_to_dataframe()
        
        if df.empty:
            return {
                "summary": "No product data available for filtering.",
                "data": [],
                "columns": []
            }
        
        print(f"📊 Loaded {len(df)} products for filtering")
        
        # Step 2: Apply filters
        filtered_df = apply_filters(df, filters, query)
        
        # Step 3: Handle aggregations if needed
        if is_aggregation_query(query):
            return handle_aggregation_query(query, df, filtered_df)
        
        # Step 4: Sort results if needed
        sorted_df = apply_sorting(filtered_df, query)
        
        # Step 5: Format response
        return format_structured_response(query, sorted_df)
        
    except Exception as e:
        print(f"❌ Error in structured query: {e}")
        return {
            "summary": f"Error processing structured query: {str(e)}",
            "data": [],
            "columns": []
        }


def handle_semantic_query(query):
    """
    Handle semantic/RAG-style queries using vector search
    """
    print(f"🔍 Handling SEMANTIC query with RAG pipeline")
    
    # Step 1: Translate query into multiple variants for better retrieval
    translated_queries = translate_query(query)
    
    # Step 2: Search vector DB with all translated queries
    search_results = search_and_filter(translated_queries, collection_suffix="json")
    
    if not search_results:
        return {
            "summary": "Sorry, I couldn't find any relevant information for your query in this JSON file.",
            "data": [],
            "columns": []
        }
    
    # Step 3: Build context string from top unique results
    context = "\n\n".join([
        f"Data:\n{doc.page_content}"
        for doc, score in search_results
    ])
    
    # Step 4: Generate response with structured JSON output
    response = generate_structured_response(query, context)
    
    # Step 5: Evaluate response relevance and filter if needed
    return response


def handle_hybrid_query(query):
    """
    Handle hybrid queries combining structured filtering with semantic search
    """
    print(f"🔀 Handling HYBRID query - combining semantic and structured approaches")
    
    try:
        # Step 1: Extract structured filters from the query using LLM
        filters = extract_structured_filters(query)
        print(f"🔧 Extracted filters for hybrid approach: {filters}")
        
        # Step 2: Load data once and apply structured filtering first (if any filters found)
        original_df = load_json_to_dataframe()
        filtered_df = original_df.copy()
        
        if not original_df.empty and filters:
            print(f"📊 Applying structured filters first...")
            filtered_df = apply_filters(original_df, filters, query)
            print(f"📊 After structured filtering: {len(filtered_df)} products remain")
        
        # Step 3: If we have meaningful structured filtering results, use semantic search on them
        if not filtered_df.empty and len(filtered_df) < len(original_df):
            # We had some structured filtering - now do semantic search on remaining products
            print(f"🔍 Running semantic search on {len(filtered_df)} pre-filtered products")
            
            # Create context from filtered products for semantic search
            product_contexts = []
            for _, product in filtered_df.iterrows():
                context = f"Product: {product['productName']} ({product['brand']}) - ₹{product['price']} - {product.get('taste', 'N/A')}"
                product_contexts.append(context)
            
            combined_context = "\n\n".join(product_contexts)
            
            # Generate response using both structured data and semantic context
            return generate_hybrid_response(query, combined_context, filtered_df)
        
        else:
            # No structured filters applied or no results - fall back to pure semantic search
            print(f"🔍 No effective structured filtering, falling back to semantic search")
            return handle_semantic_query(query)
            
    except Exception as e:
        print(f"❌ Error in hybrid query: {e}")
        # Fall back to semantic approach on error
        return handle_semantic_query(query)


def generate_hybrid_response(query, context, df):
    """
    Generate response for hybrid queries using both structured data and semantic context
    """
    HYBRID_SYSTEM_PROMPT = f"""
    You are a helpful AI assistant answering user queries about products. You have access to both:
    1. Structured product data (filtered based on user criteria)
    2. Semantic context about product tastes and descriptions
    
    Use BOTH the structured data AND the semantic context to provide a comprehensive answer.
    
    You MUST respond with a valid JSON object in this format:
    {{
      "summary": "<comprehensive answer combining both structured and semantic insights>",
      "data": [
        {{ "<field>": "<value>", ... }},
        ...
      ],
      "columns": ["<field1>", "<field2>", ...]
    }}
    
    Rules:
    - "summary": Provide insights that combine filtering results with taste/quality analysis
    - "data": Include the relevant products as structured records
    - "columns": List the field names used in data
    - If no products match, set data to [] and columns to []
    - Do NOT wrap JSON in code fences
    
    Context with filtered products:
    {context}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": HYBRID_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.3  # Slight creativity for taste analysis
        )
        
        # Return response string directly for final JSON parsing  
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating hybrid response: {e}")
        # Fallback to structured formatting
        return format_structured_response(query, df)


def generate_structured_response(query, context):
    """
    Generate structured JSON response using LLM
    """
    SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant who answers user queries based on the available context
    retrieved from a JSON data file.

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
    - "summary": always include a plain-language answer.
    - "data": include the matching records as an array of objects. If no tabular data is relevant, set to [].
    - "columns": list the keys used in the data rows (same order). If data is [], set to [].
    - Answer ONLY from the context below. Do not invent values.
    - Do NOT wrap the JSON in markdown code fences.

    Context:
    {context}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
    )
    return response.choices[0].message.content


def get_query_result_json(query):
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
            result = handle_structured_query(query, filters)
        elif query_type == "HYBRID":
            result = handle_hybrid_query(query)
        else:  # SEMANTIC (default)
            result = handle_semantic_query(query)
        
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
        print(f"❌ Error in get_query_result_json: {e}")
        return "Sorry, there was an error processing your query. Please try again."
