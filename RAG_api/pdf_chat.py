import os
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

load_dotenv()

client = OpenAI()

# Vector Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

vector_db = QdrantVectorStore.from_existing_collection(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    collection_name=os.getenv("QDRANT_COLLECTION"),
    embedding=embedding_model
)
def get_query_result_pdf(query):
    try:
        # Step 1: Fetch top-10 candidates from vector DB with similarity scores.
        # Using scores allows us to filter by relevance, not just rank.
        # Qdrant returns cosine similarity scores: higher = more relevant.
        RELEVANCE_THRESHOLD = 0.4  # Minimum score to consider a result relevant
        raw_results_with_scores = vector_db.similarity_search_with_score(query, k=10)
        print(f"\n🔍 Raw results from vector DB: {len(raw_results_with_scores)}")

        # Step 2: Filter by relevance threshold.
        # This prevents passing unrelated context to the LLM when the query
        # doesn't match the PDF content (e.g., asking about Redux in a React doc).
        relevant_results = [
            (doc, score) for doc, score in raw_results_with_scores
            if score >= RELEVANCE_THRESHOLD
        ]
        print(f"📊 Results above relevance threshold ({RELEVANCE_THRESHOLD}): {len(relevant_results)}")

        # Step 3: If no results meet the threshold, the query is out of scope for this PDF.
        if not relevant_results:
            return "Sorry, I couldn't find any relevant information for your query in this PDF. Try asking something related to the document content."

        # Step 4: Filter for unique content (diversity control).
        # Qdrant may return the same chunk with different IDs — deduplicate by content.
        unique_contents = set()
        search_results = []  # stores (doc, score) tuples
        for doc, score in relevant_results:
            if doc.page_content not in unique_contents:
                search_results.append((doc, score))
                unique_contents.add(doc.page_content)

        # Step 5: Limit to top 5 unique results to keep context concise for the LLM.
        search_results = search_results[:5]
        print(f"✅ Unique results after filtering: {len(search_results)}")

        # Step 6: Debug print each result for inspection
        for i, (doc, score) in enumerate(search_results):
            print(f"\n--- Result {i+1} ---")
            print(f"Content: {doc.page_content[:200]}")
            print(f"Page: {doc.metadata.get('page_label', 'Unknown')}")
            print(f"Similarity Score: {score:.4f}")
            print(f"Content hash: {hash(doc.page_content)}")

        # Step 7: Build context from unique results
        context = "\n\n".join([
            f"Page Content: {doc.page_content}\nPage Number: {doc.metadata.get('page_label', 'Unknown')}"
            for doc, score in search_results
        ])

        SYSTEM_PROMPT = f"""
        You are a helpful AI Assistant who answers user queries based on the available context
        retrieved from a PDF file along with page contents and page number.

        You should only answer the user based on the following context and navigate the user
        to open the right page number to know more.

        Context:
        {context}
        """

        # Step 7: Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]
        )
        answer = response.choices[0].message.content
        print(f"\n🤖: {answer}")
        return answer

    except Exception as e:
        print(f"❌ Error in get_query_result_pdf: {e}")
        return "Sorry, there was an error processing your query. Please try again."
     
