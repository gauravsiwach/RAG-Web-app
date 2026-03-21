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
        # Step 1: Get more candidates for diversity
        raw_results = vector_db.similarity_search(query, k=10)
        print(f"\n🔍 Raw results from vector DB: {len(raw_results)}")

        # Step 2: Filter for unique content (diversity control)
        unique_contents = set()
        search_results = []
        for doc in raw_results:
            if doc.page_content not in unique_contents:
                search_results.append(doc)
                unique_contents.add(doc.page_content)

        # Step 3: Limit to top 5 unique results
        search_results = search_results[:5]
        print(f"✅ Unique results after filtering: {len(search_results)}")

        # Step 4: Check if we have any results
        if not search_results:
            return "Sorry, I couldn't find any relevant information in the PDF. Try rephrasing your question."

        # Step 5: Debug print each result
        for i, doc in enumerate(search_results):
            print(f"\n--- Result {i+1} ---")
            print(f"Content: {doc.page_content[:200]}")
            print(f"Page: {doc.metadata.get('page_label', 'Unknown')}")
            print(f"Content hash: {hash(doc.page_content)}")

        # Step 6: Build context from unique results
        context = "\n\n".join([
            f"Page Content: {result.page_content}\nPage Number: {result.metadata.get('page_label', 'Unknown')}"
            for result in search_results
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
     
