from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv 
import os

load_dotenv()  

def process_pdfFile(file_path):
    print(f"Starting PDF processing for: {file_path}")
    try:
        # Load the PDF file
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Chunking the documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_docs = text_splitter.split_documents(documents)

        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )

        # Remove old collection if it exists
        from qdrant_client import QdrantClient
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_collection = os.getenv("QDRANT_COLLECTION")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            print(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Using [embedding_model] create embeddings of [split_docs] and store in DB
        vector_store = QdrantVectorStore.from_documents(
            documents=split_docs,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=qdrant_collection,
            embedding=embedding_model
        )
        print("Indexing of Documents Done...")
        return True
    except Exception as e:
        import traceback
        print(f"Error processing PDF file: {e}")
        traceback.print_exc()
        return False

def process_web_url_content(pages_content: str):
    try:
        print("Processing web URL content...")
        # Chunking the documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_contents = text_splitter.split_text(pages_content)
        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )

        # Using [embedding_model] create embeddings of [split_docs] and store in DB
        vector_store = QdrantVectorStore.from_texts(
            texts=split_contents,
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION"),
            embedding=embedding_model
        )
        print("Indexing of Documents Done...")
       
        return True
    except Exception as e:
        print(f"Error processing web URL: {e}")
        return False