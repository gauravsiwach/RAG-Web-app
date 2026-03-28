
import logging
import os
from typing import List, Optional
from dataclasses import dataclass, field
from langchain_openai import OpenAIEmbeddings
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential as SearchKeyCredential

logger = logging.getLogger("azureai_indexing")

@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    taste: Optional[str] = ""
    embedding: Optional[List[float]] = field(default_factory=list)

async def azure_ai_indexing(data: dict) -> dict:
    """
    Simple function to process JSON payload, generate embeddings, and upload to Azure AI Search.
    """
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
    AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

    if not (AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY and AZURE_SEARCH_INDEX):
        raise Exception("Azure Search config missing in environment.")

    # Flatten products
    products = []
    if isinstance(data, dict) and "categories" in data:
        for category in data.get("categories", []):
            category_name = category.get("categoryName", "")
            for prod in category.get("products", []):
                products.append(Product(
                    id=prod.get("productId", ""),
                    name=prod.get("productName", ""),
                    description=f"{prod.get('brand', '')} | {category_name}",
                    price=float(prod.get("price", 0)),
                    taste=prod.get("taste", "")
                ))
    else:
        raise Exception("Invalid JSON format. Expected 'categories' structure.")

    if not products:
        raise Exception("No products found in the JSON payload.")

    # Embedding model (langchain)
    embedding_model = OpenAIEmbeddings(model=AZURE_OPENAI_DEPLOYMENT)
    for prod in products:
        embedding_text = f"{prod.name} {prod.description} {prod.taste}".strip()
        prod.embedding = embedding_model.embed_query(embedding_text)

    # Upload to Azure Search
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=SearchKeyCredential(AZURE_SEARCH_KEY)
    )
    docs = [p.__dict__ for p in products]
    result = await search_client.upload_documents(documents=docs)
    await search_client.close()
    succeeded = [r for r in result if r.succeeded]
    failed = [r for r in result if not r.succeeded]
    return {
        "message": f"Uploaded {len(succeeded)}/{len(products)} products to Azure AI Search.",
        "total_products": len(products),
        "uploaded_count": len(succeeded),
        "failed_count": len(failed)
    }


