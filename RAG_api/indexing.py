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

        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

        # Remove old collection if it exists
        from qdrant_client import QdrantClient
        from qdrant_client.models import PayloadSchemaType
        from langchain_core.documents import Document
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            print(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Flatten JSON categories → individual product Documents with structured metadata
        documents = []
        if isinstance(data, dict) and "categories" in data:
            for category in data.get("categories", []):
                category_name = category.get("categoryName", "")
                for product in category.get("products", []):
                    promotions = product.get("promotions", [])
                    has_promotions = len(promotions) > 0
                    promo_text = ", ".join([p.get("desc", "") for p in promotions]) if promotions else "No promotions"

                    # Text for semantic search embedding
                    text = (
                        f"Product: {product.get('productName', '')} | "
                        f"Brand: {product.get('brand', '')} | "
                        f"Category: {category_name} | "
                        f"Price: ₹{product.get('price', 0)} INR | "
                        f"Taste: {product.get('taste', 'N/A')} | "
                        f"Promotions: {promo_text}"
                    )

                    doc = Document(
                        page_content=text,
                        metadata={
                            "productId": product.get("productId", ""),
                            "productName": product.get("productName", ""),
                            "brand": product.get("brand", ""),
                            "price": float(product.get("price", 0)),
                            "categoryName": category_name,
                            "taste": product.get("taste", "N/A"),
                            "hasPromotions": has_promotions,
                        }
                    )
                    documents.append(doc)
        else:
            # Fallback: generic JSON — chunk as text
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            raw = json.dumps(data, indent=2, ensure_ascii=False)
            for chunk in text_splitter.split_text(raw):
                documents.append(Document(page_content=chunk))

        # Store embeddings in Qdrant with per-product metadata
        vector_store = QdrantVectorStore.from_documents(
            documents=documents,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=qdrant_collection,
            embedding=embedding_model,
        )

        # Create payload indexes so Qdrant can filter on structured fields
        print("📋 Creating payload indexes for filterable fields...")
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.price",        field_schema=PayloadSchemaType.FLOAT)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.brand",        field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.categoryName", field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.hasPromotions", field_schema=PayloadSchemaType.BOOL)

        print(f"✅ Indexing of JSON Done... ({len(documents)} products indexed with structured metadata)")
        return True
    except Exception as e:
        import traceback
        print(f"Error processing JSON file: {e}")
        traceback.print_exc()
        return False