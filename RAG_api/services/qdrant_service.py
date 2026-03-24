"""
qdrant_service.py

Centralized Qdrant vector database client and service wrapper.
Handles vector storage, search, and collection management operations.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, PayloadSchemaType
from langchain_qdrant import QdrantVectorStore
from config.settings import settings

# Global Qdrant client instance
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create the global Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
    return _qdrant_client


class QdrantService:
    """Centralized Qdrant service for vector database operations."""
    
    def __init__(self, client: Optional[QdrantClient] = None):
        self.client = client or get_qdrant_client()
    
    def get_collection_name(self, suffix: str) -> str:
        """Generate standardized collection name with suffix."""
        return f"{settings.QDRANT_COLLECTION}_{suffix}"
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Qdrant."""
        try:
            collections = self.client.get_collections().collections
            return collection_name in [c.name for c in collections]
        except Exception as e:
            print(f"❌ Error checking collection existence: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection if it exists."""
        try:
            if self.collection_exists(collection_name):
                print(f"🗑️ Deleting collection: {collection_name}")
                self.client.delete_collection(collection_name=collection_name)
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting collection {collection_name}: {e}")
            return False
    
    def create_vector_store(
        self,
        collection_name: str,
        embedding_function,
        documents: Optional[List] = None,
        texts: Optional[List[str]] = None
    ) -> QdrantVectorStore:
        """
        Create a QdrantVectorStore from documents or texts.
        
        Args:
            collection_name: Name of the collection
            embedding_function: Embedding model instance
            documents: List of documents (for from_documents)
            texts: List of text strings (for from_texts)
            
        Returns:
            QdrantVectorStore instance
        """
        try:
            if documents is not None:
                return QdrantVectorStore.from_documents(
                    documents=documents,
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    collection_name=collection_name,
                    embedding=embedding_function,
                )
            elif texts is not None:
                return QdrantVectorStore.from_texts(
                    texts=texts,
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    collection_name=collection_name,
                    embedding=embedding_function,
                )
            else:
                raise ValueError("Either documents or texts must be provided")
                
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
            raise
    
    def get_vector_store(
        self, 
        collection_name: str, 
        embedding_function
    ) -> QdrantVectorStore:
        """
        Connect to existing QdrantVectorStore collection.
        
        Args:
            collection_name: Name of the existing collection
            embedding_function: Embedding model instance
            
        Returns:
            QdrantVectorStore instance connected to existing collection
        """
        try:
            return QdrantVectorStore.from_existing_collection(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                collection_name=collection_name,
                embedding=embedding_function,
            )
        except Exception as e:
            print(f"❌ Error connecting to existing collection {collection_name}: {e}")
            raise
    
    def create_payload_index(
        self,
        collection_name: str,
        field_name: str,
        field_type: PayloadSchemaType
    ) -> bool:
        """
        Create a payload index for filtering on structured fields.
        
        Args:
            collection_name: Name of the collection
            field_name: Dot-separated field path (e.g., "metadata.price")
            field_type: PayloadSchemaType enum value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📋 Creating payload index: {field_name} ({field_type.value})")
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_type
            )
            return True
        except Exception as e:
            print(f"❌ Error creating payload index {field_name}: {e}")
            return False
    
    def query_points(
        self,
        collection_name: str,
        query: List[float],
        query_filter: Optional[Filter] = None,
        limit: int = 10,
        score_threshold: float = None,
        with_payload: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using Qdrant query_points API.
        
        Args:
            collection_name: Name of the collection
            query: Query vector embedding
            query_filter: Optional Qdrant filter for structured filtering
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            with_payload: Include payload data in results
            
        Returns:
            List of search results with scores and payloads
        """
        try:
            results = self.client.query_points(
                collection_name=collection_name,
                query=query,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=with_payload
            )
            
            # Convert to standardized format
            formatted_results = []
            for point in results.points:
                result = {
                    "id": point.id,
                    "score": point.score,
                }
                if with_payload:
                    result["payload"] = point.payload
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error querying points in {collection_name}: {e}")
            return []
    
    def count_points(self, collection_name: str) -> int:
        """Get the number of points in a collection."""
        try:
            info = self.client.get_collection(collection_name)
            return info.points_count
        except Exception as e:
            print(f"❌ Error counting points in {collection_name}: {e}")
            return 0