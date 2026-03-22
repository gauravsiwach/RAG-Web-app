from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv 
import os
import json

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
        qdrant_collection = os.getenv("QDRANT_COLLECTION") + "_pdf"
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
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_collection = os.getenv("QDRANT_COLLECTION") + "_url"

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

        # Remove old collection if it exists
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            print(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Using [embedding_model] create embeddings of [split_contents] and store in DB
        vector_store = QdrantVectorStore.from_texts(
            texts=split_contents,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=qdrant_collection,
            embedding=embedding_model
        )
        print("Indexing of Documents Done...")

        return True
    except Exception as e:
        import traceback
        print(f"Error processing web URL: {e}")
        traceback.print_exc()
        return False


def process_json_file(file_path):
    print(f"Starting JSON processing for: {file_path}")
    try:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_collection = os.getenv("QDRANT_COLLECTION") + "_json"

        # Load and parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Flatten JSON to a list of text chunks
        raw_texts = []
        if isinstance(data, list):
            for item in data:
                raw_texts.append(json.dumps(item, indent=2, ensure_ascii=False))
        elif isinstance(data, dict):
            for key, value in data.items():
                raw_texts.append(f"{key}:\n{json.dumps(value, indent=2, ensure_ascii=False)}")
        else:
            raw_texts.append(str(data))

        # Further chunk any long texts
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_texts = []
        for raw in raw_texts:
            split_texts.extend(text_splitter.split_text(raw))

        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

        # Remove old collection if it exists
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            print(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Store embeddings in Qdrant
        vector_store = QdrantVectorStore.from_texts(
            texts=split_texts,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=qdrant_collection,
            embedding=embedding_model,
        )
        print(f"Indexing of JSON Done... ({len(split_texts)} chunks)")
        return True
    except Exception as e:
        import traceback
        print(f"Error processing JSON file: {e}")
        traceback.print_exc()
        return False