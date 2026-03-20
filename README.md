# RAG Chatbot Web Application

A full-stack **Retrieval-Augmented Generation (RAG)** chatbot that allows users to upload PDFs or provide web URLs, then ask intelligent questions about the content using AI-powered responses.

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