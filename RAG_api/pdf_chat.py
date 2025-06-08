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
    url="https://d166e4e5-a5d6-4547-92fa-a72bd2e46f50.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.RMPCpZQEUzQURo0N_Bxo7bQTvu4VOJdpm79eHD-Itw0",
    collection_name="learning_vectors",
    embedding=embedding_model
)
def get_query_result_pdf(query):
    search_results = vector_db.similarity_search(query)

    context = "".join([f"Page Content: {result.page_content}\n Page Number:{result.metadata['page_label']}" for result in search_results])
    print("System propmt is ready---")
    SYSTEM_PROMPT = f"""
        You are a helpfull AI Assistant who asnweres user query based on the available context
        retrieved from a PDF file along with page_contents and page number.

        You should only ans the user based on the following context and navigate the user
        to open the right page number to know more.

        Context:
        {context}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            { "role": "system", "content": SYSTEM_PROMPT },
            { "role": "user", "content": query },
        ]
    )
    answer = response.choices[0].message.content
    print(f"🤖: {answer}")
    return answer
     
