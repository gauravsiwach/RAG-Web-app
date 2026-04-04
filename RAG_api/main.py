# Load environment variables first, before any other imports
from dotenv import load_dotenv
load_dotenv()

# Azure AI Search hybrid chat endpoint
from azure_search_hybrid import azure_search_hybrid_chat
from fastapi import Body
from fastapi import FastAPI, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os

# Multi-language support
from language_translation import (
    process_multilingual_query,
    process_multilingual_response,
    get_supported_languages
)

from indexing import process_pdfFile
from indexing import process_web_url_content
from indexing import process_json_file
from pdf_chat import get_query_result_pdf
from web_url_chat import get_query_result_web
from json_chat import get_query_result_json
from json_chat_hybrid import get_query_result_json_hybrid
from web_crawler import crawl_webpage
from web_crawler import crawl_all_pages
from azureai_indexing import azure_ai_indexing


app = FastAPI(
    title="RAG API",
    description="A comprehensive API for Retrieval-Augmented Generation with support for PDF, JSON, Web content, and Azure AI Search integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers


# Azure AI Search indexing endpoint (Swagger-friendly)
from typing import List
from pydantic import BaseModel

class ProductModel(BaseModel):
    productId: str
    productName: str
    brand: str
    price: float
    taste: str = ""

class CategoryModel(BaseModel):
    categoryName: str
    products: List[ProductModel]

class IndexingPayload(BaseModel):
    categories: List[CategoryModel]

class AzureSearchChatRequest(BaseModel):
    message: str

@app.post("/azure_search_chat")
async def azure_search_chat_endpoint(request: AzureSearchChatRequest):
    """
    Accepts a user message, performs hybrid search on Azure AI Search, and returns LLM-judged results.
    """
    return await azure_search_hybrid_chat(request.message)


@app.post("/azure-ai-indexing/")
async def azure_ai_indexing_endpoint(payload: IndexingPayload):
    """
    Accepts a JSON payload with product data, generates embeddings, and uploads to Azure AI Search.
    """
    try:
        result = await azure_ai_indexing(payload.dict())
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "RAG API is running"}

@app.get("/supported-languages")
def get_languages():
    """
    Returns list of supported languages for multi-language queries.
    """
    return {"languages": get_supported_languages()}

# Request model
class ChatRequest(BaseModel):
    message: str
    version: str = "v2"  # "v1" = json_chat (Pandas+Vector), "v2" = json_chat_hybrid (Pure Qdrant)

# Response model
class ChatResponse(BaseModel):
    reply: str
@app.post("/pdf_chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    print("Received request:", request)
    print("User message:", request.message)
    user_message = request.message
    result = get_query_result_pdf(user_message)
    return {"reply": result}  

@app.post("/web_url_chat", response_model=ChatResponse) 
def web_chat_api(request: ChatRequest):
    print("Received request:", request)
    print("User message:", request.message)
    user_message = request.message
    result = get_query_result_web(user_message)
    return {"reply": result}

@app.post("/json_chat", response_model=ChatResponse)
def json_chat_api(request: ChatRequest):
    print("Received request:", request)
    print("User message:", request.message)
    print(f"Chat engine version: {request.version}")
    if request.version == "v1":
        result = get_query_result_json(request.message)
    else:  # v2 (default)
        result = get_query_result_json_hybrid(request.message)
    return {"reply": result}


@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure directory exists
        os.makedirs("uploaded_files", exist_ok=True)

        file_content = file.file.read()
        file_path = f"uploaded_files/{file.filename}"
        with open(file_path, "wb") as f:
            bytes_written = f.write(file_content)

        if bytes_written == 0:
            raise HTTPException(status_code=500, detail="Failed to write file content.")

        # call the function to process the file here
        # and save vector into db
        result=process_pdfFile(file_path)

        if result is False:
            raise HTTPException(status_code=500, detail="Failed to process the file.")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                     "filename": file.filename, 
                     "size": bytes_written, 
                     "message": "File uploaded successfully and indexing in done."
                     }
        )       

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/upload-json")
def upload_json_file(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Only .json files are allowed.")

        os.makedirs("uploaded_files", exist_ok=True)

        file_content = file.file.read()
        file_path = f"uploaded_files/{file.filename}"
        with open(file_path, "wb") as f:
            bytes_written = f.write(file_content)

        if bytes_written == 0:
            raise HTTPException(status_code=500, detail="Failed to write file content.")

        result = process_json_file(file_path)

        if result is False:
            raise HTTPException(status_code=500, detail="Failed to process the JSON file.")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "filename": file.filename,
                "size": bytes_written,
                "message": "JSON file uploaded and indexed successfully."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

class UrlPayload(BaseModel):
    url: HttpUrl

@app.post("/web-url")
async def process_web_url(payload: UrlPayload):
    try:
        print("Received URL:", payload.url)
        url_str = str(payload.url) 
        print("calling crawl_webpage")
        page_content_result = await crawl_webpage(url_str)
        
        print("crawl_webpage result:", page_content_result)

        if not page_content_result:
            raise HTTPException(status_code=500, detail="No content found for the URL.")
        
        page_content = list(page_content_result.values())[0]
        #crawl_all_pages(url_str)
        # call the function to process the file here
        # and save vector into db
        result=process_web_url_content(page_content)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to process the webpage.")

        return result
    except Exception as e:
        print(f"Exception in /web-url: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# uvicorn main:app --reload --host 0.0.0.0 --port 8000
# uvicorn main:app --reload --host 0.0.0.0 --port 9000
 