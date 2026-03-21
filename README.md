# RAG Chatbot Web Application

A full-stack **Retrieval-Augmented Generation (RAG)** chatbot that allows users to upload PDFs or provide web URLs, then ask intelligent questions about the content using AI-powered responses.

---

## 🌟 Features

- 📄 **PDF Upload & Processing** — Upload PDFs up to 50MB with drag-and-drop
- 🌐 **Web URL Crawling** — Extract and process content from any public web page
- 🧠 **Query Translation Pipeline** — Expands queries using Multi-Query, Step-Back, and Sub-Query strategies for better retrieval
- 🔍 **Relevance Filtering** — Cosine similarity threshold prevents passing unrelated context to the LLM
- 💬 **Intelligent Chat Interface** — Context-aware Q&A with page number references
- ⚙️ **Configurable Text Chunking** — Adjust chunk size (100–4000) and overlap (0–1000)
- 🚫 **Duplicate Removal** — Automatically deduplicates retrieved chunks before context building

---

## 🏗️ Architecture

### Backend (RAG_api) — Python FastAPI
| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI server, 4 API endpoints, CORS config |
| `pdf_chat.py` | PDF query handler — orchestrates translation → search → LLM |
| `web_url_chat.py` | Web URL query handler |
| `query_translation.py` | 3 query translation strategies (Multi-Query, Step-Back, Sub-Query) |
| `vector_search.py` | Similarity search, relevance filtering, deduplication |
| `indexing.py` | Document chunking, embedding, Qdrant vector storage |
| `web_crawler.py` | Async web scraping with httpx and BeautifulSoup |

### Frontend (text-rag-app) — React + Vite
| File | Responsibility |
|------|---------------|
| `DashboardLayout.jsx` | Main 2-column layout (sidebar + chat), mode switching, state management |
| `PdfUploader.jsx` | Drag-and-drop PDF upload, validation, processing |
| `WebUrlInput.jsx` | URL input form and processing |

---

## 🔄 Data Flow

### PDF Mode
```
User uploads PDF
  → POST /upload (multipart)
  → PyPDFLoader → RecursiveCharacterTextSplitter (1000/200)
  → OpenAI text-embedding-3-large
  → DELETE old Qdrant collection → Store new vectors
  → Chat enabled ✅

User asks question
  → POST /pdf_chat {message}
  → translate_query() → [original + multi-query variants]
  → search_and_filter() → similarity_search_with_score per query
  → filter score ≥ 0.4 → deduplicate → top 5 chunks
  → Build context → GPT-4o-mini → Return answer
```

### Web URL Mode
```
User enters URL
  → POST /web-url {url}
  → crawl_webpage() → BeautifulSoup text extraction
  → RecursiveCharacterTextSplitter → OpenAI embeddings
  → Append to Qdrant collection
  → Chat enabled ✅

User asks question
  → POST /web_url_chat {message}
  → Direct similarity_search(k=5) → context → GPT-4o-mini
```

---

## 🧠 Query Translation Strategies

Defined in `query_translation.py`, these run **before** vector search to improve retrieval coverage:

| Strategy | What it does | Example |
|----------|-------------|---------|
| **Multi-Query** | Rewrites query into 3 alternative phrasings | "What is JSX?" → ["Explain JSX in React", "How JSX works", "JSX syntax"] |
| **Step-Back** | Generates a broader, abstract version | "What does useState return?" → "How do React hooks work?" |
| **Sub-Query** | Decomposes complex question into sub-questions | "What is JSX and how differs from HTML?" → ["What is JSX?", "JSX vs HTML?"] |

### Test Results (React Quick Start PDF)
| Category | Count | % |
|----------|-------|---|
| ✅ Direct matches | 5/15 | 33% |
| 🔄 Found via translation | 5/15 | 33% |
| ❌ Not in document (correct) | 5/15 | 33% |
| **Total success** | **10/15** | **67%** |

> See full results in [SampleData/rag_query_test_results.md](SampleData/rag_query_test_results.md)

---

## 🚀 Setup

### Prerequisites
- **Python 3.9+**
- **Node.js 14+**
- **OpenAI API Key** — for embeddings (`text-embedding-3-large`) and LLM (`gpt-4o-mini`)
- **Qdrant Cloud Account** — vector database (or self-hosted Qdrant instance)

### 1. Environment Configuration

The `.env` file is **not committed to git** for security reasons.

Create a `.env` file manually in the `RAG_api` directory:

```bash
# Copy the example file and fill in your values
cp RAG_api/.env.example RAG_api/.env
```

Or create it manually with the following keys:

```env
QDRANT_URL="YOUR_QDRANT_URL_HERE"
QDRANT_API_KEY="YOUR_QDRANT_API_KEY_HERE"
QDRANT_COLLECTION="YOUR_QDRANT_COLLECTION_HERE"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
```

> ⚠️ **Never commit your `.env` file.** It contains secret API keys. The `.gitignore` is already configured to exclude it.

### 2. Backend Setup
```bash
cd RAG_api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at `http://localhost:8000`

### 3. Frontend Setup
```bash
cd text-rag-app
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## 📋 API Endpoints

| Endpoint | Method | Description | Request |
|----------|--------|-------------|---------|
| `/upload` | POST | Upload and index a PDF file | `multipart/form-data` with `file`, `chunk_size`, `chunk_overlap` |
| `/pdf_chat` | POST | Query indexed PDF content | `{message: string}` |
| `/web-url` | POST | Crawl and index a web page | `{url: string}` |
| `/web_url_chat` | POST | Query indexed web content | `{message: string}` |

---

## 📁 Project Structure

```
project-root/
├── RAG_api/                        # Backend
│   ├── main.py                     # FastAPI server & routes
│   ├── pdf_chat.py                 # PDF query orchestration
│   ├── web_url_chat.py             # Web URL query handler
│   ├── query_translation.py        # Multi-Query, Step-Back, Sub-Query
│   ├── vector_search.py            # Search + filter + deduplicate
│   ├── indexing.py                 # Chunk, embed, store in Qdrant
│   ├── web_crawler.py              # Async web scraping
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # ⚠️ Not committed — create from .env.example
│   ├── .env.example                # Template with required keys
│   └── uploaded_files/             # PDF storage directory
│
├── text-rag-app/                   # Frontend
│   ├── src/
│   │   ├── App.jsx                 # Root component
│   │   ├── DashboardLayout.jsx     # Main layout + chat + state
│   │   ├── PdfUploader.jsx         # PDF drag-drop upload
│   │   ├── WebUrlInput.jsx         # URL input form
│   │   ├── main.jsx                # React entry point
│   │   ├── App.css                 # Styling
│   │   └── index.css               # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── SampleData/
│   └── rag_query_test_results.md   # RAG pipeline test results
│
└── README.md
```

---

## 🛠️ Key Dependencies

### Backend
```
fastapi, uvicorn           — API server
langchain, langchain-openai, langchain-qdrant  — RAG pipeline
qdrant-client              — Vector database client
openai                     — Embeddings + LLM
pypdf                      — PDF text extraction
httpx, beautifulsoup4      — Web crawling
python-dotenv              — Environment variables
```

### Frontend
```
react@19, react-dom        — UI framework
react-toastify             — Toast notifications
vite                       — Build tool with hot reload
```

---

## 🔧 Configuration

### Chunking Parameters (configurable from UI)
| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| Chunk Size | 100–4000 | 1000 | Larger = more context per chunk |
| Chunk Overlap | 0–1000 | 200 | Higher = less information loss at boundaries |

### Relevance Threshold (`vector_search.py`)
```python
RELEVANCE_THRESHOLD = 0.4  # Cosine similarity minimum
```
| Score | Meaning |
|-------|---------|
| > 0.85 | Highly relevant |
| 0.70–0.85 | Moderately relevant |
| 0.4–0.70 | Weakly relevant (included) |
| < 0.4 | Filtered out |

---

## 🚨 Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Duplicate search results | Same PDF uploaded multiple times | Old collection is now auto-deleted before re-indexing |
| "Not found" for valid queries | Score below threshold | Lower `RELEVANCE_THRESHOLD` in `vector_search.py` |
| Too many irrelevant results | Threshold too low | Raise `RELEVANCE_THRESHOLD` to 0.6–0.7 |
| Upload fails | File > 50MB or not PDF | Check file size and type |
| Chat disabled after upload | Upload failed silently | Check backend terminal for error logs |

---

## 🔐 Security Notes

- `.env` file excluded from git via `.gitignore`
- CORS currently allows all origins — restrict `allow_origins` for production
- API keys stored only in `.env`, never hardcoded
- File upload limited to PDFs with 50MB size cap


## 🌟 Features

- 📄 **PDF Upload & Processing** - Upload PDFs up to 50MB with drag-and-drop interface
- 🌐 **Web URL Crawling** - Extract and process content from web pages
- 💬 **Intelligent Chat Interface** - Ask questions about your documents with context-aware responses
- ⚙️ **Configurable Text Chunking** - Adjust chunk size (100-4000) and overlap (0-1000) for optimal results
- 🔍 **Vector Similarity Search** - Find relevant content using semantic search
- 📊 **Real-time Feedback** - Loading indicators, toast notifications, and typing animations
- 🎨 **Modern UI** - React-based responsive interface with dual-pane layout

## 🏗️ Architecture

### Backend (RAG_api)
- **Framework**: FastAPI with Python
- **Document Processing**: LangChain for PDF parsing and text chunking
- **Vector Database**: Qdrant Cloud for storing embeddings
- **AI Models**: OpenAI GPT-4-mini for responses, text-embedding-3-large for vectors
- **Web Scraping**: Custom crawler using httpx and BeautifulSoup

### Frontend (text-rag-app)
- **Framework**: React 19 with Vite build tool
- **Styling**: Custom CSS with responsive design
- **State Management**: React hooks
- **Notifications**: react-toastify for user feedback

### Data Flow
```
User uploads PDF/URL → Backend processes & chunks content → 
OpenAI creates embeddings → Qdrant stores vectors → 
User asks question → Similarity search finds relevant chunks → 
GPT-4 generates contextual response
```

## 🚀 Quick Setup

### Prerequisites
- **Python 3.9+**
- **Node.js 14+**
- **OpenAI API Key**
- **Qdrant Cloud Account** (or local Qdrant instance)

### 1. Environment Configuration
Create a `.env` file in the `RAG_api` directory:

```env
QDRANT_URL="YOUR_QDRANT_URL_HERE"
QDRANT_API_KEY="YOUR_QDRANT_API_KEY_HERE"
QDRANT_COLLECTION="YOUR_QDRANT_COLLECTION_HERE"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd RAG_api

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd text-rag-app

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload and process PDF files |
| `/pdf_chat` | POST | Ask questions about uploaded PDFs |
| `/web-url` | POST | Process content from web URLs |
| `/web_url_chat` | POST | Ask questions about web content |

## 🔧 Configuration Options

### Text Chunking Parameters
- **Chunk Size**: 100-4000 tokens (default: 1000)
- **Chunk Overlap**: 0-1000 tokens (default: 200)
- **Validation**: Overlap cannot exceed chunk size

### Supported File Types
- **PDF**: Up to 50MB
- **Web URLs**: Any publicly accessible webpage

## 📁 Project Structure

```
project-root/
├── RAG_api/                    # Backend API
│   ├── main.py                 # FastAPI server and routes
│   ├── indexing.py             # Document processing & vector storage
│   ├── pdf_chat.py             # PDF query handling
│   ├── web_url_chat.py         # Web URL query handling
│   ├── web_crawler.py          # Web scraping utilities
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   ├── uploaded_files/         # PDF storage directory
│   └── __pycache__/           # Python cache
│
├── text-rag-app/              # Frontend Application
│   ├── src/
│   │   ├── App.jsx             # Root component
│   │   ├── DashboardLayout.jsx # Main UI layout
│   │   ├── PdfUploader.jsx     # PDF upload component
│   │   ├── WebUrlInput.jsx     # URL input component
│   │   ├── main.jsx            # React entry point
│   │   ├── App.css             # Styling
│   │   └── index.css           # Global styles
│   ├── public/                 # Static assets
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite configuration
│   └── eslint.config.js        # Linting rules
│
└── README.md                   # This file
```

## 🛠️ Key Dependencies

### Backend (76 total packages)
```
fastapi==0.115.12              # Web framework
langchain==0.3.25               # LLM integration
langchain-openai==0.3.19        # OpenAI connector
langchain-qdrant==0.2.0         # Vector database
qdrant-client==1.14.2           # Qdrant client
openai==1.82.1                  # OpenAI API
pypdf==5.6.0                    # PDF processing
httpx==0.28.1                   # HTTP client
beautifulsoup4                  # HTML parsing
uvicorn==0.34.3                 # ASGI server
```

### Frontend (3 main packages)
```
react==19.1.0                   # UI framework
react-dom==19.1.0               # DOM rendering
react-toastify==11.0.5          # Notifications
vite==6.3.5                     # Build tool
```

## 🎯 Usage Guide

### 1. PDF Upload Mode
1. Select "📄 PDF File" mode in the sidebar
2. Drag & drop a PDF or click to browse files
3. Adjust chunk size and overlap if needed
4. Wait for processing completion
5. Start asking questions about the PDF content

### 2. Web URL Mode
1. Select "🌐 Web URL" mode in the sidebar
2. Enter a valid web URL
3. Configure chunking parameters
4. Click submit and wait for processing
5. Ask questions about the web page content

### 3. Chat Interface
- Type your question in the input field at the bottom
- Press Enter or click Send
- View responses in the chat area
- Chat history is maintained during the session
- Context from your documents is automatically included

## 🔍 Advanced Features

### Smart Text Processing
- **Recursive Character Text Splitter**: Intelligently splits documents while preserving context
- **Overlap Management**: Prevents information loss at chunk boundaries
- **Token-aware Chunking**: Optimized for LLM token limits

### Vector Search
- **Semantic Similarity**: Find relevant content based on meaning, not just keywords
- **Qdrant Integration**: High-performance vector database for fast retrieval
- **Embedding Model**: OpenAI's text-embedding-3-large for superior accuracy

### Error Handling
- **File Validation**: Size limits, type checking, error messages
- **API Resilience**: Graceful handling of network issues and API errors
- **User Feedback**: Real-time status updates and notifications

## 🚨 Troubleshooting

### Common Issues

**Backend won't start:**
- Check if port 8000 is available
- Verify all environment variables are set in `.env`
- Ensure Python dependencies are installed

**Frontend connection errors:**
- Verify backend is running on port 8000
- Check CORS settings in FastAPI
- Ensure no firewall blocking local connections

**Upload failures:**
- Check file size (50MB limit)
- Verify PDF is not corrupted or password-protected
- Ensure sufficient disk space

**Chat responses are poor:**
- Adjust chunk size (try 500-1500 for better context)
- Increase chunk overlap (try 10-20% of chunk size)
- Verify document content is text-based (not just images)

### Performance Tips
- **Optimal chunk size**: 1000-1500 tokens for most documents
- **Overlap ratio**: 10-20% of chunk size for good context preservation
- **Document quality**: Clean, well-formatted PDFs work best
- **Question specificity**: More specific questions yield better answers

## 🔐 Security Notes

- **API Keys**: Never commit `.env` file to version control
- **CORS**: Currently allows all origins (adjust for production)
- **File Upload**: Only accepts PDFs, with size limits enforced
- **Rate Limiting**: Consider adding for production deployment

## 🚢 Deployment

### Development
```bash
# Backend
cd RAG_api && uvicorn main:app --reload --port 8000

# Frontend
cd text-rag-app && npm run dev
```

### Production Build
```bash
# Frontend build
cd text-rag-app && npm run build

# Serve built files with your preferred web server
# Backend can run with uvicorn in production mode (remove --reload)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure you have proper licenses for all API services used.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Verify your API keys and environment setup
3. Review the console logs for error messages
4. Ensure all dependencies are properly installed

---

**Happy RAG Chatting! 🚀**