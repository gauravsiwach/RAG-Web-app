"""
vector_search.py

Handles vector DB search, relevance filtering, and deduplication.
Used by pdf_chat.py, web_url_chat.py, and json_chat.py for retrieval.
"""

import os
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Vector Embeddings — shared embedding model for all search operations
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

# Minimum similarity score to consider a result relevant.
# Qdrant cosine similarity: 1.0 = identical, 0.0 = unrelated.
RELEVANCE_THRESHOLD = 0.4


def _get_vector_db(collection_suffix: str) -> QdrantVectorStore:
    """Connect to the Qdrant collection for the given source type."""
    base = os.getenv("QDRANT_COLLECTION")
    collection_name = f"{base}_{collection_suffix}"
    return QdrantVectorStore.from_existing_collection(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=collection_name,
        embedding=embedding_model,
    )


def search_and_filter(translated_queries: list[str], collection_suffix: str = "pdf") -> list[tuple]:
    """
    Runs similarity search for each translated query against the correct collection,
    applies relevance threshold filtering, deduplicates by content,
    and returns the top 5 unique (doc, score) tuples sorted by score descending.

    Args:
        translated_queries:  List of query strings (original + translated variants)
        collection_suffix:   Collection postfix to target — "pdf", "url", or "json"

    Returns:
        List of (Document, score) tuples — unique, relevant, ranked by score
    """
    vector_db = _get_vector_db(collection_suffix)

    # Step 1: Run vector search for each query and collect all raw results
    all_raw_results: list[tuple] = []
    for q in translated_queries:
        results = vector_db.similarity_search_with_score(q, k=5)
        all_raw_results.extend(results)

    print(f"\n🔍 Total raw results across all queries: {len(all_raw_results)}")

    # Debug: Print sample raw results content (first 3 only)
    for i, (doc, score) in enumerate(all_raw_results[:3]):
        print(f"\n📄 Sample Result {i+1}:")
        print(f"   Score: {score:.4f}")
        print(f"   Content: {doc.page_content[:100]}...")
        print(f"   Metadata: {doc.metadata}")
    

    # Step 2: Filter by relevance threshold — removes chunks unrelated to the query
    relevant_results = [
        (doc, score) for doc, score in all_raw_results
        if score >= RELEVANCE_THRESHOLD
    ]
    print(f"📊 Results above relevance threshold ({RELEVANCE_THRESHOLD}): {len(relevant_results)}")

    if not relevant_results:
        return []

    # Step 3: Sort by score descending so highest-scoring chunk wins deduplication
    relevant_results.sort(key=lambda x: x[1], reverse=True)

    # Step 4: Deduplicate by content — multiple translated queries may return the same chunk
    unique_contents = set()
    search_results = []
    for doc, score in relevant_results:
        if doc.page_content not in unique_contents:
            search_results.append((doc, score))
            unique_contents.add(doc.page_content)

    # Step 5: Limit to top 5 unique results to keep LLM context concise
    search_results = search_results[:5]
    print(f"✅ Final unique results: {len(search_results)}")

    # Step 6: Debug print for inspection
    for i, (doc, score) in enumerate(search_results):
        print(f"\n--- Result {i+1} ---")
        print(f"Content: {doc.page_content[:200]}")
        print(f"Page: {doc.metadata.get('page_label', 'Unknown')}")
        print(f"Similarity Score: {score:.4f}")

    return search_results
