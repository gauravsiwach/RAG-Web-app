# RAG Chatbot API Backend

A comprehensive **Retrieval-Augmented Generation (RAG)** system built with FastAPI, supporting multiple document types and advanced query processing capabilities.

## 🚀 Features

### 📄 **PDF Chat**
- Upload and query PDF documents
- Page-aware responses with navigation hints
- Multi-query translation for better retrieval
- Automatic text chunking and indexing

### 🌐 **Web URL Chat**  
- Crawl and query web page content
- Async content extraction and processing
- Web-optimized response generation
- Support for various web content formats

### 📊 **JSON Product Chat**
- **V1**: Pandas-based structured + semantic search
- **V2**: Pure Qdrant hybrid search with native filtering
- Automatic query classification (STRUCTURED/SEMANTIC/HYBRID)
- Natural language filter extraction

## 🏗️ Architecture

### Modular Package Structure
```
RAG_api/
├── config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py            # Centralized settings & env vars
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── guardrails.py         # Input validation & output filtering
│   ├── query_translation.py  # Multi-query expansion
│   └── search_and_filter.py  # Vector search operations
├── services/                  # External service integrations
│   ├── __init__.py
│   ├── indexing_service.py   # Document processing & indexing
│   ├── openai_service.py     # LLM & embedding operations
│   ├── qdrant_service.py     # Vector database operations
│   └── web_crawler_service.py # Web content extraction
├── handlers/                  # Domain-specific request handlers
│   ├── __init__.py
│   ├── json_handler.py       # JSON product data queries
│   ├── json_hybrid_handler.py # Advanced hybrid search
│   ├── pdf_handler.py        # PDF document queries
│   └── web_url_handler.py    # Web URL queries
├── api/                      # FastAPI routes & endpoints
│   ├── __init__.py
│   ├── models.py             # Pydantic request/response models
│   └── endpoints/
│       ├── __init__.py
│       ├── chat.py           # Chat endpoints
│       ├── health.py         # Health check endpoints
│       └── upload.py         # File upload endpoints
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
└── uploaded_files/          # File storage directory
```

### RAG Pipeline
```
Query Input → Query Translation → Vector Search → Relevance Filtering → LLM Generation → Guardrails → Response
```

## 🛠️ Technologies

- **Framework**: FastAPI + Uvicorn
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: text-embedding-3-large (1536 dimensions)
- **Vector Database**: Qdrant Cloud
- **Document Processing**: PyPDF2, BeautifulSoup4
- **Data Processing**: Pandas, NumPy
- **HTTP Client**: httpx (async)
- **Environment**: Python 3.11+

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11 or higher
- OpenAI API key
- Qdrant Cloud instance

### Installation

1. **Clone the repository**
```bash
git clone <your-repo>
cd RAG_api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=chat_bot_vectors_1
```

5. **Run the application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Health Check
```http
GET /health
```

### Chat Endpoints

#### PDF Chat
```http
POST /api/chat/pdf
Content-Type: application/json

{
    "query": "What is the main topic of this document?"
}
```

#### Web URL Chat
```http
POST /api/chat/web-url
Content-Type: application/json

{
    "query": "Summarize the content from the uploaded URL"
}
```

#### JSON Product Chat (V1 - Pandas)
```http
POST /api/chat/json
Content-Type: application/json

{
    "query": "Show me all products under ₹50"
}
```

#### JSON Product Chat (V2 - Hybrid Search)
```http
POST /api/chat/json-hybrid
Content-Type: application/json

{
    "query": "Find sweet beverages under ₹40"
}
```

### Upload Endpoints

#### Upload PDF
```http
POST /api/upload/pdf
Content-Type: multipart/form-data

Form field: file (PDF file)
```

#### Upload Web URL
```http
POST /api/upload/web-url
Content-Type: application/json

{
    "url": "https://example.com/article"
}
```

#### Upload JSON Data
```http
POST /api/upload/json
Content-Type: multipart/form-data

Form field: file (JSON file)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model name | gpt-4o-mini |
| `EMBEDDING_MODEL` | Embedding model | text-embedding-3-large |
| `QDRANT_URL` | Qdrant instance URL | Required |
| `QDRANT_API_KEY` | Qdrant API key | Required |
| `QDRANT_COLLECTION` | Collection name | chat_bot_vectors_1 |
| `MAX_FILE_SIZE` | Max upload size (bytes) | 52428800 (50MB) |
| `RELEVANCE_THRESHOLD` | Search relevance cutoff | 0.4 |

### Application Settings
Modify `config/settings.py` to adjust:
- Chunk size and overlap for document processing
- API host and port configuration
- CORS settings for production
- Search parameters and thresholds

## 💡 Usage Examples

### Query Classification Examples

**Structured Queries** (automatically routed to structured search):
```
"Show me all products under ₹50"
"List beverages by Coca-Cola"
"Find snacks between ₹20 and ₹40"
```

**Semantic Queries** (automatically routed to semantic search):
```
"I want something refreshing and cold"
"Find me healthy snack options"
"What do you recommend for a party?"
```

**Hybrid Queries** (combines both approaches):
```
"Find sweet beverages under ₹40"
"Show me spicy snacks from Indian brands"
"Recommend healthy drinks below ₹30"
```

### Response Formats

The API returns responses compatible with the frontend JsonResultRenderer:

```json
{
    "reply": "{\"summary\": \"Found 5 products matching criteria\", \"data\": [...], \"columns\": [...]}"
}
```

## 🔍 Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
```bash
black .
flake8 .
```

### Adding New Features

1. **New Document Type**: Add handler in `handlers/` package
2. **New Service Integration**: Add service in `services/` package  
3. **New Endpoint**: Add route in `api/endpoints/` package
4. **Configuration**: Update `config/settings.py`

## 📖 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all packages have `__init__.py` files
2. **Environment Variables**: Check `.env` file exists and contains required keys
3. **Qdrant Connection**: Verify Qdrant URL and API key
4. **File Upload Issues**: Check file size limits and upload directory permissions

### Debug Mode
Enable detailed logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Considerations

- Store API keys securely in environment variables
- Restrict CORS origins in production
- Implement rate limiting for production deployment
- Validate and sanitize user inputs
- Use HTTPS in production

## 📈 Performance Optimization

- **Caching**: Implement Redis for query result caching
- **Database**: Use connection pooling for Qdrant
- **Async**: Leverage FastAPI's async capabilities
- **Chunking**: Optimize document chunk size for your use case

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Built with ❤️ using FastAPI, OpenAI, and Qdrant**