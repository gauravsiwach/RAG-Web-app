import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

def classify_query_type(query):
    """
    Uses LLM to classify user query into:
    - STRUCTURED: exact filtering, counts, aggregations, numerical comparisons
    - SEMANTIC: descriptive, subjective criteria, taste, quality
    - HYBRID: combination of both structured and semantic aspects
    """
    try:
        CLASSIFICATION_PROMPT = """
        You are a query classifier for a product database system. Classify the user query into one of these categories:

        **STRUCTURED**: Queries requiring exact database operations like:
        - Numerical filters: "under ₹20", "price > 50", "less than 100"
        - Counts/Aggregations: "how many", "total count", "average price", "sum"
        - Exact matches: "brand = Coca-Cola", "category is Beverages"
        - Sorting: "cheapest", "most expensive", "sort by price"

        **SEMANTIC**: Queries requiring similarity search and subjective understanding:
        - Descriptive qualities: "sweet", "refreshing", "crispy", "tangy", "spicy"
        - Subjective preferences: "best", "good for", "tasty", "healthy", "popular"
        - Vague concepts: "products like this", "similar to", "recommend"

        **HYBRID**: Queries combining both structured filtering AND semantic aspects:
        - "Cheapest sweet snacks" (price + taste)
        - "Refreshing drinks under ₹50" (semantic + price filter)
        - "Best Coca-Cola products" (brand filter + subjective ranking)

        Product attributes available:
        - price, currency, brand, productName, categoryName
        - taste (descriptive text for food products)
        - promotions

        Respond with ONLY one word from this list:
        STRUCTURED | SEMANTIC | HYBRID

        Do NOT add anything else.
        
        """

        # Call LLM classifier
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user", "content": f"Classify this query: {query}"},
            ],
            temperature=0.0,  # Consistent classification
            max_tokens=10     # Only need one word
        )

        classification = response.choices[0].message.content.strip().upper()
        
        # Validate response
        if classification in ["STRUCTURED", "SEMANTIC", "HYBRID"]:
            print(f"\n🔍 Query classified as: {classification}")
            return classification
        else:
            print(f"⚠️ Invalid classification '{classification}', defaulting to SEMANTIC")
            return "SEMANTIC"

    except Exception as e:
        print(f"❌ Error in query classification: {e}")
        # Default to SEMANTIC if classifier fails
        return "SEMANTIC"


def extract_structured_filters(query):
    """
    Extract structured filters from query using LLM for better natural language understanding
    """
    try:
        # Use LLM to extract structured filters
        filters = extract_filters_with_llm(query)
        print(f"🧠 LLM extracted filters: {filters}")
        return filters
    except Exception as e:
        print(f"⚠️ LLM filter extraction failed: {e}, falling back to basic extraction")
        # Simple fallback for critical cases
        return extract_basic_filters(query)


def extract_filters_with_llm(query):
    """
    Use LLM to extract structured filters from natural language query
    """
    FILTER_EXTRACTION_PROMPT = """
    You are a query parser that extracts structured filters from natural language product queries.
    
    Extract the following filter types from the user query and return as JSON:
    
    **Price Filters:**
    - price_min: minimum price (for "above", "over", "more than", "greater than", ">", "at least")
    - price_max: maximum price (for "under", "below", "less than", "up to", "<", "at most")
    - price_exact: exact price match (for "exactly", "costs", "priced at")
    
    **Brand Filters:**
    - brand: exact brand name from this list [Coca-Cola, Pepsi, Sprite, Fanta, Nestlé, Amul, Lay's, Kurkure, Doritos, Haldiram, Pringles, Bingo, Too Yumm, Real, Tropicana, Britannia, Kwality Walls, Yakult, Epigamia, Red Bull, Dove, Clinic Plus, Pantene, H&S, Colgate, Closeup, Lux, Dettol, Lifebuoy, Nivea, Mother Dairy, Surf Excel, Ariel, Tide, Vim, Harpic, Lizol, Colin, Good Knight, Hit]
    
    **Category Filters:**
    - category: category name [Beverages, Snacks, Dairy, Personal Care, Household]
    
    **Promotion Filters:**
    - has_promotions: true/false for products with offers/discounts/deals/promotions
    
    **Count/Aggregation Indicators:**
    - is_count_query: true for "how many", "count", "total number"
    - is_aggregation_query: true for "average", "mean", "sum", "cheapest", "most expensive"
    
    **Product Search Terms:**
    - search_term: product name or search keyword (for "list of", "show me", "find", product names)
    
    Rules:
    1. Extract numerical values without currency symbols (₹, INR, rupees)
    2. Map common category terms: "drinks"→"Beverages", "chips"→"Snacks"
    3. Normalize brand names to exact matches from the list above
    4. If no filters found, return empty object {}
    5. For price ranges like "between X and Y", use both price_min and price_max
    
    Examples:
    "Show products under ₹50" → {"price_max": 50}
    "Coca-Cola drinks above 30 rupees" → {"brand": "Coca-Cola", "price_min": 30}
    "Snacks between 20 and 40" → {"category": "Snacks", "price_min": 20, "price_max": 40}
    "Products with discounts" → {"has_promotions": true}
    "How many Pepsi products cost more than ₹25" → {"brand": "Pepsi", "price_min": 25, "is_count_query": true}
    "Cheapest beverages" → {"category": "Beverages", "is_aggregation_query": true}
    "Show me all products that cost greater than ₹50" → {"price_min": 50}
    "Give me list of water" → {"search_term": "water"}
    "Show me chocolate items" → {"search_term": "chocolate"}
    "Find juice products" → {"search_term": "juice"}
    "List all milk products" → {"search_term": "milk"}
    
    Respond ONLY with the JSON object. No explanations or markdown fencing.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FILTER_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Extract filters from this query: {query}"},
            ],
            temperature=0.0,  # Consistent extraction
            max_tokens=200   # Enough for filter extraction
        )
        
        filters = json.loads(response.choices[0].message.content)
        return filters if filters else {}
        
    except Exception as e:
        print(f"❌ Error in LLM filter extraction: {e}")
        return {}


def extract_basic_filters(query):
    """
    Basic fallback filter extraction using simple keyword matching
    """
    filters = {}
    query_lower = query.lower()
    
    # Basic brand detection
    if "coca-cola" in query_lower:
        filters["brand"] = "Coca-Cola"
    elif "pepsi" in query_lower:
        filters["brand"] = "Pepsi"
    elif "amul" in query_lower:
        filters["brand"] = "Amul"
    
    # Basic category detection  
    if any(word in query_lower for word in ["snacks", "chips"]):
        filters["category"] = "Snacks"
    elif any(word in query_lower for word in ["drinks", "beverages"]):
        filters["category"] = "Beverages"
    elif "dairy" in query_lower:
        filters["category"] = "Dairy"
    
    # Basic promotion detection
    if any(word in query_lower for word in ["discount", "offer", "deal", "promotion"]):
        filters["has_promotions"] = True
        
    # Basic aggregation detection
    if any(word in query_lower for word in ["how many", "count", "total"]):
        filters["is_count_query"] = True
    elif any(word in query_lower for word in ["cheapest", "most expensive", "average"]):
        filters["is_aggregation_query"] = True
    
    return filters