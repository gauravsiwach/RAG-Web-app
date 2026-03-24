"""
upload.py

File upload and indexing endpoints.
Handles PDF, JSON, and web URL processing with vector indexing.
"""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from ..models import UploadResponse, UrlRequest, ErrorResponse
from services import process_pdfFile, process_json_file, process_web_url_content, crawl_webpage
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",  
    tags=["Upload & Indexing"],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Processing failed"}
    }
)


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload PDF Document",
    description="Upload and index a PDF document for chat queries."
)
def upload_pdf_file(file: UploadFile = File(...)):
    """
    Upload and process PDF documents for vector indexing.
    
    Features:
    - File size validation (max 50MB)
    - PDF format validation
    - Text extraction and chunking
    - Vector embedding generation
    - Qdrant storage with metadata
    
    Args:
        file: PDF file to upload and process
        
    Returns:
        UploadResponse: Upload status and file information
        
    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Check file size
        file_content = file.file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file not allowed"
            )
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            bytes_written = f.write(file_content)
        
        logger.info(f"PDF file saved: {file.filename} ({bytes_written} bytes)")
        
        # Process and index the PDF
        logger.info(f"Starting PDF processing: {file.filename}")
        result = process_pdfFile(file_path)
        
        if result is False:
            logger.error(f"PDF processing failed: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process the PDF file"
            )
        
        logger.info(f"PDF processing completed successfully: {file.filename}")
        
        return UploadResponse(
            filename=file.filename,
            size=bytes_written,
            message="PDF file uploaded successfully and indexing is done."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PDF upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF upload failed: {str(e)}"
        )


@router.post(
    "/upload-json",
    response_model=UploadResponse,
    summary="Upload JSON Data", 
    description="Upload and index structured JSON product data for queries."
)
def upload_json_file(file: UploadFile = File(...)):
    """
    Upload and process JSON product data for vector indexing.
    
    Features:
    - JSON format validation
    - Structured data flattening
    - Metadata extraction (price, brand, category)
    - Vector embedding with payload indexing
    - Qdrant storage with filterable fields
    
    Args:
        file: JSON file to upload and process
        
    Returns:
        UploadResponse: Upload status and file information
        
    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
            
        if not file.filename.lower().endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON files are supported"
            )
        
        # Check file size
        file_content = file.file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file not allowed"
            )
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            bytes_written = f.write(file_content)
        
        logger.info(f"JSON file saved: {file.filename} ({bytes_written} bytes)")
        
        # Process and index the JSON
        logger.info(f"Starting JSON processing: {file.filename}")
        result = process_json_file(file_path)
        
        if result is False:
            logger.error(f"JSON processing failed: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process the JSON file"
            )
        
        logger.info(f"JSON processing completed successfully: {file.filename}")
        
        return UploadResponse(
            filename=file.filename,
            size=bytes_written,
            message="JSON file uploaded and indexed successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in JSON upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JSON upload failed: {str(e)}"
        )


@router.post(
    "/web-url",
    summary="Process Web URL",
    description="Crawl and index a web page for chat queries."
)
async def process_web_url_endpoint(request: UrlRequest):
    """
    Crawl and process web page content for vector indexing.
    
    Features:
    - URL validation and normalization
    - Async web crawling with error handling
    - Content extraction and cleaning
    - Text chunking and embedding
    - Qdrant storage for retrieval
    
    Args:
        request: URL request with target web page
        
    Returns:
        dict: Processing status and result information
        
    Raises:
        HTTPException: If crawling or processing fails
    """
    try:
        url_str = str(request.url)
        logger.info(f"Processing web URL: {url_str}")
        
        # Crawl the webpage
        logger.info("Starting web crawling...")
        page_content_result = await crawl_webpage(url_str)
        
        if not page_content_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content found for the URL. Please check the URL and try again."
            )
        
        # Extract content (first page from result dict)
        page_content = list(page_content_result.values())[0]
        if not page_content or not page_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty content extracted from URL"
            )
        
        logger.info(f"Extracted content ({len(page_content)} chars), starting indexing...")
        
        # Process and index the content
        result = process_web_url_content(page_content)
        
        if not result:
            logger.error(f"Web content processing failed for URL: {url_str}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process the webpage content"
            )
        
        logger.info(f"Web URL processing completed successfully: {url_str}")
        
        return {
            "status": "success",
            "url": url_str,
            "content_length": len(page_content),
            "message": "Web page crawled and indexed successfully.",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in web URL processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Web URL processing failed: {str(e)}"
        )


# Additional utility endpoints
@router.get(
    "/upload/limits",
    summary="Upload Limits",
    description="Get information about file upload limits and supported formats."
)
def get_upload_limits():
    """
    Get upload limits and supported file formats.
    
    Returns:
        dict: Upload configuration and limits
    """
    return {
        "max_file_size_bytes": settings.MAX_FILE_SIZE,
        "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
        "upload_directory": settings.UPLOAD_DIR,
        "supported_formats": {
            "pdf": {
                "extensions": [".pdf"],
                "description": "PDF documents for text extraction and indexing"
            },
            "json": {
                "extensions": [".json"],
                "description": "Structured product data for hybrid search"
            },
            "web_url": {
                "protocols": ["http", "https"],
                "description": "Web pages for content crawling and indexing"
            }
        },
        "processing_features": {
            "pdf": ["text_extraction", "chunking", "vector_embedding", "page_metadata"],
            "json": ["data_flattening", "metadata_indexing", "payload_filtering", "hybrid_search"],
            "web_url": ["content_crawling", "text_cleaning", "chunking", "vector_embedding"]
        }
    }