#  uvicorn main:app --reload 

from fastapi import FastAPI, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os

 

from indexing import process_pdfFile
from indexing import process_web_url_content
from pdf_chat import get_query_result_pdf
from web_url_chat import get_query_result_web
from web_crawler import crawl_webpage
from web_crawler import crawl_all_pages


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str

# Response model
class ChatResponse(BaseModel):
    reply: str
@app.post("/pdf_chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    print("Received request:", request)
    print("User message:", request.message)
    user_message = request.message
    result=get_query_result_pdf(user_message)
    return {"reply":result}  

@app.post("/web_url_chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    print("Received request:", request)
    print("User message:", request.message)
    user_message = request.message
    result=get_query_result_web(user_message)
    return {"reply":result}   



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

 