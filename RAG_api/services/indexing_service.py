"""
indexing_service.py

Document indexing service for PDF, JSON, and web content.
Handles vector embedding and Qdrant storage with consistent configuration.
"""

import json
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
from config.settings import settings

logger = logging.getLogger(__name__)


def process_pdf_file(file_path: str) -> bool:
    """
    Process and index PDF document for vector search.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Starting PDF processing for: {file_path}")
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
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )

        # Remove old collection if it exists
        qdrant_collection = settings.QDRANT_COLLECTION + "_pdf"
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            logger.info(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Create embeddings and store in Qdrant
        vector_store = QdrantVectorStore.from_documents(
            documents=split_docs,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=qdrant_collection,
            embedding=embedding_model
        )
        logger.info("✅ PDF indexing completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error processing PDF file: {e}", exc_info=True)
        return False


def process_web_url_content(pages_content: str) -> bool:
    """
    Process and index web content for vector search.
    
    Args:
        pages_content: Raw web page content text
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Processing web URL content...")
    try:
        qdrant_collection = settings.QDRANT_COLLECTION + "_url"

        # Chunking the documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_contents = text_splitter.split_text(pages_content)

        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )

        # Remove old collection if it exists
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            logger.info(f"Deleting old collection: {qdrant_collection}")
            client.delete_collection(collection_name=qdrant_collection)

        # Create embeddings and store in Qdrant
        vector_store = QdrantVectorStore.from_texts(
            texts=split_contents,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=qdrant_collection,
            embedding=embedding_model
        )
        logger.info("✅ Web URL indexing completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error processing web URL: {e}", exc_info=True)
        return False


def process_json_file(file_path: str) -> bool:
    """
    Process and index JSON product data for hybrid vector search.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Starting JSON processing for: {file_path}")
    try:
        qdrant_collection = settings.QDRANT_COLLECTION + "_json"

        # Load and parse JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vector Embeddings
        embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )

        # Remove old collection if it exists
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        collections = client.get_collections().collections
        if qdrant_collection in [c.name for c in collections]:
            logger.info(f"Deleting old collection: {qdrant_collection}")
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
            # Fallback: generic JSON → chunk as text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            raw = json.dumps(data, indent=2, ensure_ascii=False)
            for chunk in text_splitter.split_text(raw):
                documents.append(Document(page_content=chunk))

        # Store embeddings in Qdrant with per-product metadata
        vector_store = QdrantVectorStore.from_documents(
            documents=documents,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=qdrant_collection,
            embedding=embedding_model,
        )

        # Create payload indexes so Qdrant can filter on structured fields
        logger.info("📋 Creating payload indexes for filterable fields...")
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.price", field_schema=PayloadSchemaType.FLOAT)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.brand", field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.categoryName", field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=qdrant_collection, field_name="metadata.hasPromotions", field_schema=PayloadSchemaType.BOOL)
        
        logger.info(f"✅ JSON indexing completed successfully ({len(documents)} products indexed with structured metadata)")
        return True
    except Exception as e:
        logger.error(f"❌ Error processing JSON file: {e}", exc_info=True)
        return False


# Legacy function aliases for backward compatibility
process_pdfFile = process_pdf_file  # Legacy alias
process_web_url_content = process_web_url_content  # Already using snake_case
process_json_file = process_json_file  # Already using snake_case