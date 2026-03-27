"""
azure_search_hybrid.py

Hybrid Search over Azure AI Search with LLM Judgement
- Accepts user query
- Generates embedding
- Calls Azure AI Search (hybrid: vector + text)
- Optionally applies filters
- Uses LLM to summarize/judge results (like json_chat_hybrid)
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

from query_translation import translate_query
from query_classifier import classify_query_type, extract_structured_filters
from response_judge import evaluate_and_filter_response
from guardrails import guardrails_input, guardrails_output

load_dotenv()

# Initialize embedding model
embedding_model = OpenAIEmbeddings(model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small"))

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

async def azure_hybrid_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Hybrid search in Azure AI Search: vector + text + optional filters
    """
    print(f"[azure_hybrid_search] Query: {query}")
    # Step 0: Translate query into variants (use all variants for hybrid search)
    translated_queries = translate_query(query)
    print(f"[azure_hybrid_search] Translated queries: {translated_queries}")
    all_results = []
    seen_ids = set()
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )
    try:
        for variant_query in translated_queries:
            print(f"[azure_hybrid_search] Processing variant: {variant_query}")
            parsed = parse_hybrid_query(variant_query)
            print(f"[azure_hybrid_search] Parsed: {parsed}")
            semantic_query = parsed["semantic_query"]
            filters = parsed["filters"]

            # Step 2: Build filter string for Azure Search
            filter_str = build_azure_filter(filters)
            print(f"[azure_hybrid_search] Filter string: {filter_str}")

            search_kwargs = {
                "top": limit,
                # 'vector' argument removed for text-only search compatibility
                "filter": filter_str if filter_str else None,
                "query_type": "semantic" if semantic_query else "simple",
                "search": semantic_query or "*"
            }
            # Remove None values
            search_kwargs = {k: v for k, v in search_kwargs.items() if v is not None}
            print(f"[azure_hybrid_search] Search kwargs: {search_kwargs}")
            try:
                response = await search_client.search(**search_kwargs)
                async for doc in response:
                    # Deduplicate by id if possible
                    doc_id = str(doc.get('id', ''))
                    if doc_id and doc_id in seen_ids:
                        continue
                    if doc_id:
                        seen_ids.add(doc_id)
                    print(f"[azure_hybrid_search] Got doc: {doc}")
                    all_results.append(doc)
            except Exception as e:
                print(f"[azure_hybrid_search] Error during Azure Search for variant '{variant_query}': {e}")
    finally:
        await search_client.close()
    print(f"[azure_hybrid_search] Results count: {len(all_results)}")
    return all_results[:limit]

def parse_hybrid_query(query: str) -> Dict[str, Any]:
    # Use the same logic as json_chat_hybrid
    try:
        client = OpenAI()  # Create client after load_dotenv() has run
        HYBRID_PARSE_PROMPT = (
            "You are an expert AI assistant for a product search engine. "
            "Given a user query, extract two things: "
            "1. semantic_query: the natural language part to use for semantic/vector search (paraphrase or clarify if needed). "
            "2. filters: a JSON object of structured filters (like category, brand, price, etc.) if present, else an empty object. "
            "\n\n"
            "Return ONLY a valid JSON object with these keys: 'semantic_query' (string or null) and 'filters' (object). "
            "If the query is just a broad request (e.g., 'show me cold drinks'), set filters to {{}} and semantic_query to the main intent. "
            "If the query includes specifics (e.g., 'cold drinks under 50 rupees from Pepsi'), extract those as filters. "
            "\n\n"
            "Examples:"
            "\nUser: 'show me cold drinks'\nOutput: {{\"semantic_query\": \"cold drinks\", \"filters\": {{}}}}"
            "\nUser: 'list all Pepsi cold drinks under 50 rupees'\nOutput: {{\"semantic_query\": \"cold drinks\", \"filters\": {{\"brand\": \"Pepsi\", \"price_lt\": 50}}}}"
            "\nUser: 'give me Coca-Cola juices above 100'\nOutput: {{\"semantic_query\": \"juices\", \"filters\": {{\"brand\": \"Coca-Cola\", \"price_gt\": 100}}}}"
            "\nUser: 'what are some examples of cold beverages?'\nOutput: {{\"semantic_query\": \"cold beverages\", \"filters\": {{}}}}"
            "\n\nIf unsure, set filters to {{}}. Do not invent fields."
        )
        print(f"[parse_hybrid_query] Calling LLM with query: {query}")
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
        print(f"[parse_hybrid_query] LLM raw response: {response.choices[0].message.content}")
        parsed = json.loads(response.choices[0].message.content)
        print(f"[parse_hybrid_query] Parsed output: {parsed}")
        return {
            "semantic_query": parsed.get("semantic_query"),
            "filters": parsed.get("filters", {})
        }
    except Exception as e:
        print(f"❌ Error parsing hybrid query: {e}")
        return {"semantic_query": query, "filters": {}}

def build_azure_filter(filters: Dict[str, Any]) -> Optional[str]:
    # Build OData filter string for Azure Search
    conditions = []
    if "categoryName" in filters:
        conditions.append(f"categoryName eq '{filters['categoryName']}'")
    if "brand" in filters:
        conditions.append(f"brand eq '{filters['brand']}'")
    if "price_lt" in filters:
        conditions.append(f"price lt {filters['price_lt']}")
    if "price_gt" in filters:
        conditions.append(f"price gt {filters['price_gt']}")
    # Add more as needed
    return " and ".join(conditions) if conditions else None

async def azure_search_hybrid_chat(query: str) -> str:
    """
    Main entry point for Azure AI Search hybrid chat
    """
    print(f"[azure_search_hybrid_chat] Received query: {query}")
    # Guardrail input
    input_check = guardrails_input(query)
    print(f"[azure_search_hybrid_chat] Guardrail input check: {input_check}")
    if not input_check["passed"]:
        print(f"[azure_search_hybrid_chat] Guardrail failed: {input_check['message']}")
        return input_check["message"]
    # Hybrid search
    results = await azure_hybrid_search(query, limit=5)
    print(f"[azure_search_hybrid_chat] Hybrid search results: {results}")
    if not results:
        print(f"[azure_search_hybrid_chat] No results found.")
        return json.dumps({
            "summary": "No products found matching your criteria.",
            "data": [],
            "columns": []
        })
    # Format for LLM
    context_parts = []
    for doc in results:
        try:
            context_parts.append(json.dumps(doc, default=str))
        except Exception as e:
            print(f"[azure_search_hybrid_chat] Error serializing doc: {e}")
    combined_context = "\n\n".join(context_parts)
    print(f"[azure_search_hybrid_chat] Combined context for LLM: {combined_context[:500]}... (truncated)")
    # LLM summarization
    SEMANTIC_SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant who answers user queries based on the available context
    retrieved from Azure AI Search using hybrid (vector + text) search.
    You MUST respond ONLY with a valid JSON object in the following format:
    {{
      "summary": "<one or two sentence answer to the user query>",
      "data": [{{ "<field>": "<value>", ... }}, ...],
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
    {combined_context}
    """
    try:
        client = OpenAI()  # Create client after load_dotenv() has run
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SEMANTIC_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.2
        )
        print(f"[azure_search_hybrid_chat] LLM response: {response.choices[0].message.content}")
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error generating semantic response: {e}")
        return json.dumps({
            "summary": "Error generating response from Azure AI Search results.",
            "data": [],
            "columns": []
        })
