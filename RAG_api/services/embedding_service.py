"""
embedding_service.py

Centralized text embedding service using OpenAI embeddings.
Handles embedding generation with consistent configuration and caching.
"""

from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from config.settings import settings

# Global embedding model instance
_embedding_model: Optional[OpenAIEmbeddings] = None


def get_embedding_model() -> OpenAIEmbeddings:
    """Get or create the global embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
    return _embedding_model


class EmbeddingService:
    """Centralized embedding service for text vectorization."""
    
    def __init__(self, embedding_model: Optional[OpenAIEmbeddings] = None):
        self.model = embedding_model or get_embedding_model()
    
    def embed_query(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single query text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values or None if failed
        """
        try:
            if not text or not text.strip():
                return None
                
            embedding = self.model.embed_query(text)
            print(f"🔗 Generated embedding for: '{text[:50]}...' (dim={len(embedding)})")
            return embedding
            
        except Exception as e:
            print(f"❌ Error generating embedding for text: {e}")
            return None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
                
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return []
            
            embeddings = self.model.embed_documents(valid_texts)
            print(f"🔗 Generated {len(embeddings)} document embeddings (dim={len(embeddings[0]) if embeddings else 0})")
            return embeddings
            
        except Exception as e:
            print(f"❌ Error generating document embeddings: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension (e.g., 3072 for text-embedding-3-large)
        """
        try:
            # Generate a test embedding to get dimension
            test_embedding = self.embed_query("test")
            return len(test_embedding) if test_embedding else 0
        except Exception as e:
            print(f"❌ Error getting embedding dimension: {e}")
            # Return known dimension for text-embedding-3-large
            return 3072 if settings.EMBEDDING_MODEL == "text-embedding-3-large" else 1536
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        try:
            import numpy as np
            
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return dot_product / (norm_a * norm_b)
            
        except Exception as e:
            print(f"❌ Error calculating cosine similarity: {e}")
            return 0.0
    
    def batch_embed_with_validation(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings in batches with validation.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per batch
            
        Returns:
            List of embedding vectors
        """
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                print(f"🔄 Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                
                batch_embeddings = self.embed_documents(batch)
                if len(batch_embeddings) != len(batch):
                    print(f"⚠️ Warning: Expected {len(batch)} embeddings, got {len(batch_embeddings)}")
                
                all_embeddings.extend(batch_embeddings)
            
            print(f"✅ Generated {len(all_embeddings)} embeddings total")
            return all_embeddings
            
        except Exception as e:
            print(f"❌ Error in batch embedding: {e}")
            return []