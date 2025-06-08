from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv 
import os

load_dotenv()  

def process_pdfFile(file_path):
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

        # Using [embedding_model] create embeddings of [split_docs] and store in DB
        vector_store = QdrantVectorStore.from_documents(
            documents=split_docs,
            url="db_endpoint", 
            api_key="db_eky",
            collection_name="learning_vectors",
            embedding=embedding_model
        )
        print("Indexing of Documents Done...")
        return True
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return False

def process_web_url_content(pages_content: str):
    try:
        print("Processing web URL content...")
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

        # Using [embedding_model] create embeddings of [split_docs] and store in DB
        vector_store = QdrantVectorStore.from_texts(
            texts=split_contents,
           url="db_endpoint", 
            api_key="db_eky",
            collection_name="learning_vectors1",
            embedding=embedding_model
        )
        print("Indexing of Documents Done...")
       
        return True
    except Exception as e:
        print(f"Error processing web URL: {e}")
        return False
