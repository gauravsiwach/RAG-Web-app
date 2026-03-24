"""
Application settings and configuration management.

Centralizes all environment variables and application constants in one place.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Centralized application settings"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-large"
    
    # Qdrant Configuration  
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "chat_bot_vectors_1")
    
    # File Upload Settings
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR = "uploaded_files"
    
    # Search & RAG Settings
    RELEVANCE_THRESHOLD = 0.4
    MAX_QUERY_LENGTH = 2000
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    
    # FastAPI Settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ALLOWED_ORIGINS = ["*"]  # Restrict this in production
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required environment variables are set"""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("QDRANT_URL", cls.QDRANT_URL),
            ("QDRANT_API_KEY", cls.QDRANT_API_KEY),
        ]
        
        missing = []
        for name, value in required_vars:
            if not value:
                missing.append(name)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True


# Create settings instance
settings = Settings()

# Validate on import (will raise error if missing required vars)
try:
    settings.validate()
    print("✅ Configuration loaded and validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    # Don't raise during import to allow testing, but log the error