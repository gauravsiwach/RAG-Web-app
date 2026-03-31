# RAG Chatbot Web Application

A full-stack **Retrieval-Augmented Generation (RAG)** chatbot that supports intelligent Q&A over PDFs, web pages, and structured JSON data — powered by OpenAI GPT-4o-mini and Qdrant vector search.

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Upload & Chat** | Upload PDFs up to 50MB via drag-and-drop. Documents are chunked, embedded, and stored in Qdrant for semantic Q&A. |
| 🌐 **Web URL Crawling** | Scrape any public web page using async httpx + BeautifulSoup, then index and chat with its content. |
| 🗂️ **JSON Data Chat — V1 Classic** | Upload structured product JSON; query it with Pandas DataFrame filtering + LangChain vector search. |
| ⚡ **JSON Data Chat — V2 Hybrid** | Same data, upgraded engine: single Qdrant `query_points()` call combining semantic vector + structured metadata filters. |
| 🧠 **Multi-Query Translation** | Each query is expanded into 4 variants before retrieval. Results are merged, deduplicated, and ranked to maximize recall. |
| 🔀 **Smart Query Routing** | LLM-based classifier (`query_classifier.py`) detects whether a query is STRUCTURED, SEMANTIC, or HYBRID and routes accordingly. |
| 🔍 **Relevance Filtering** | Cosine similarity threshold (≥ 0.4) filters out low-quality chunks before they reach the LLM, reducing hallucinations. |
| 🛡️ **Input/Output Guardrails** | Comprehensive validation layer with injection detection, length limits, and LLM-as-Judge relevance checking. |
| ⚖️ **LLM-as-Judge** | After every response, a second LLM call rates relevance. If the answer is off-topic, a polite fallback is returned instead. |
| 💬 **Structured JSON Responses** | JSON chat responses use a `{summary, data[], columns[]}` schema that auto-renders as styled HTML tables in the UI. |
| ⚙️ **Configurable Chunking** | Chunk size (100–4000) and overlap (0–1000) are adjustable from the sidebar before indexing. |
| 🚫 **Duplicate Removal** | Retrieved chunks are deduplicated across all query variants before context is built for the LLM. |
| 💾 **Use Existing Data** | A toggle lets users skip re-upload and chat with previously indexed data directly. |

---

## 🏗️ Architecture

### Backend (`RAG_api/`) — Python FastAPI

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI server, 7 API endpoints, CORS config, V1/V2 routing |
| `indexing.py` | Document chunking, embedding, Qdrant storage, payload index creation |
| `pdf_chat.py` | PDF query orchestration: translate → search → LLM → judge |
| `web_url_chat.py` | Web URL query: translate → search → LLM |
| `json_chat.py` | **JSON V1**: Pandas filtering + vector search |
| `json_chat_hybrid.py` | **JSON V2**: Pure Qdrant hybrid (semantic + structured filters) |
| `query_translation.py` | Multi-Query: generates 4 query variants for better retrieval |
| `query_classifier.py` | LLM-based query classification (STRUCTURED / SEMANTIC / HYBRID) |
| `vector_search.py` | Similarity search, relevance filter (≥ 0.4), deduplication, top-5 |
| `guardrails.py` | Input validation (injection detection, length limits) + Output relevance validation |
| `web_crawler.py` | Async web scraping (httpx + BeautifulSoup) |

### Frontend (`text-rag-app/src/`) — React 19 + Vite

| Component | Responsibility |
|-----------|---------------|
| `DashboardLayout.jsx` | Main 2-column layout, mode switching, V1/V2 toggle, chat state |
| `PdfUploader.jsx` | Drag-and-drop PDF upload with 50MB validation and toast feedback |
| `WebUrlInput.jsx` | URL input form with async processing |
| `JsonUploader.jsx` | JSON file upload with last-indexed timestamp |
| `JsonResultRenderer.jsx` | Renders structured `{summary, data[], columns[]}` as HTML tables |
| `ApiStatusBadge.jsx` | Health check indicator (polls `/health` every 30s) |
| `UseExistingToggle.jsx` | Skip re-upload to reuse previously indexed data |
| `config.js` | `API_BASE_URL = "http://localhost:8000"` |

---

## �️ Security & Validation

### Guardrails System (`guardrails.py`)

Comprehensive input/output validation layer that protects against malicious queries and ensures response quality:

**Input Guardrails (Fast, No LLM Calls):**
- ✅ **Empty Query Detection** — Rejects blank/whitespace-only inputs
- ✅ **Length Limits** — Configurable maximum query length (default: 2000 chars)
- ✅ **Injection Prevention** — Regex patterns detect prompt injection and SQL injection attempts
- ✅ **Early Rejection** — Malicious queries blocked before any processing

**Output Guardrails (LLM-Based):**
- ✅ **Relevance Validation** — LLM-as-Judge ensures responses address the actual query
- ✅ **Context Grounding** — Verifies answers are based on provided context, not hallucinated
- ✅ **Fallback Responses** — Helpful suggestions when content isn't relevant

**Integration Pattern:**
```python
# All chat handlers follow this pattern:
input_check = guardrails_input(query)
if not input_check["passed"]:
    return input_check["message"]

# ... process query ...

evaluated_response = guardrails_output(query, response, context)
return evaluated_response
```

---

## �🔄 Data Flow

### PDF Mode
```
Upload PDF → POST /upload (multipart)
  → PyPDFLoader → RecursiveCharacterTextSplitter (1000/200)
  → OpenAI text-embedding-3-large
  → Delete old {COLLECTION}_pdf → Store vectors in Qdrant

User query → POST /pdf_chat {message}
  → guardrails_input() → validate query
  → translate_query() → 4 query variants
  → search_and_filter("pdf") → cosine ≥ 0.4 → dedup → top 5 chunks
  → GPT-4o-mini with context → guardrails_output() → Response
```

### Web URL Mode
```
Enter URL → POST /web-url {url}
  → crawl_webpage() → BeautifulSoup text extraction
  → Chunk → Embed → Store in {COLLECTION}_url

User query → POST /web_url_chat {message}
  → guardrails_input() → validate query
  → similarity_search(k=5) → context → GPT-4o-mini → guardrails_output() → Response
```

### JSON Mode — V1 Classic (Pandas + Vector)
```
Upload JSON → POST /upload-json {file}
  → Flatten categories → products → Document per product
  → Store page_content + metadata in {COLLECTION}_json
  → Create Qdrant payload indexes (price, brand, categoryName, hasPromotions)

User query → POST /json_chat {message, version: "v1"}
  → guardrails_input() → validate query
  → classify_query_type() → STRUCTURED | SEMANTIC | HYBRID

  STRUCTURED: load JSON from disk → Pandas filter → format results
  SEMANTIC:   translate_query() → vector search → LLM → guardrails_output()
  HYBRID:     Pandas filter first → semantic search on subset → LLM → guardrails_output()
```

### JSON Mode — V2 Hybrid (Pure Qdrant)
```
Same indexing as V1

User query → POST /json_chat {message, version: "v2"}
  → guardrails_input() → validate query
  → classify_query_type() → STRUCTURED | SEMANTIC | HYBRID

  STRUCTURED: build_qdrant_filter() → single Qdrant query_points() call
  SEMANTIC:   embed query → Qdrant vector search → LLM → guardrails_output()
  HYBRID:     parse_hybrid_query() → embed semantic part + build filter
              → single Qdrant call (vector + filter combined)
              → LLM → guardrails_output() → Response
```

---

## 🧠 Query Translation

Implemented in `query_translation.py`. Each user query is expanded into **4 variants** before vector search:

```
"Suggest refreshing drinks"
  → "Suggest refreshing drinks"                  (original)
  → "What are cool and refreshing beverages?"    (variant 1)
  → "Can you recommend thirst-quenching drinks?" (variant 2)
  → "What drinks would help me feel refreshed?"  (variant 3)
```

All 4 are searched against Qdrant. Results are merged, deduplicated, and ranked by score.

---

## 🗂️ JSON Query Classification

Each JSON query is automatically classified and routed:

| Type | Example Query | Handler |
|------|--------------|---------|
| **STRUCTURED** | "Products under ₹50", "List all Coca-Cola items" | Direct filter (Pandas V1 / Qdrant V2) |
| **SEMANTIC** | "Suggest refreshing drinks", "Best sweet snacks" | Vector similarity search |
| **HYBRID** | "Sweet drinks under ₹40", "Amul products with offers" | Filter + semantic combined |

---

## 🚀 Setup

### Prerequisites
- Python 3.9+
- Node.js 14+
- OpenAI API Key
- Qdrant Cloud account (or self-hosted Qdrant)

### 1. Environment Configuration

Create `RAG_api/.env`:
```env
OPENAI_API_KEY=sk-proj-...
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION=chat_bot_vectors_1
```

> ⚠️ Never commit `.env` to git. It's already in `.gitignore`.

### 2. Backend
```bash
cd RAG_api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API available at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

### 3. Frontend
```bash
cd text-rag-app
npm install
npm run dev
```
App available at `http://localhost:5173`

---

## 📋 API Endpoints

| Endpoint | Method | Request Body | Description |
|----------|--------|-------------|-------------|
| `/health` | GET | — | Server health check |
| `/upload` | POST | `FormData(file)` | Upload and index a PDF |
| `/upload-json` | POST | `FormData(file)` | Upload and index a JSON file |
| `/web-url` | POST | `{url: string}` | Crawl and index a web page |
| `/pdf_chat` | POST | `{message: string}` | Query indexed PDF |
| `/web_url_chat` | POST | `{message: string}` | Query indexed web content |
| `/json_chat` | POST | `{message: string, version: "v1"\|"v2"}` | Query JSON data (V1 Classic or V2 Hybrid) |

---

## 📁 Project Structure

```
project-root/
├── RAG_api/                        # Backend
│   ├── main.py                     # FastAPI server & routes
│   ├── indexing.py                 # Chunk, embed, store in Qdrant
│   ├── pdf_chat.py                 # PDF query orchestration
│   ├── web_url_chat.py             # Web URL query handler
│   ├── json_chat.py                # JSON V1 (Pandas + Vector)
│   ├── json_chat_hybrid.py         # JSON V2 (Pure Qdrant Hybrid)
│   ├── query_translation.py        # Multi-Query expansion
│   ├── query_classifier.py         # STRUCTURED/SEMANTIC/HYBRID classifier
│   ├── vector_search.py            # Search, filter, deduplicate
│   ├── guardrails.py               # Input/Output validation & security
│   ├── web_crawler.py              # Async web scraping
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # ⚠️ Not committed — create manually
│   └── uploaded_files/             # Uploaded file storage
│
├── text-rag-app/                   # Frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── DashboardLayout.jsx     # Main layout, chat, V1/V2 toggle
│   │   ├── PdfUploader.jsx
│   │   ├── WebUrlInput.jsx
│   │   ├── JsonUploader.jsx
│   │   ├── JsonResultRenderer.jsx  # Renders JSON responses as tables
│   │   ├── ApiStatusBadge.jsx
│   │   ├── UseExistingToggle.jsx
│   │   └── config.js               # API_BASE_URL
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🛠️ Key Dependencies

### Backend
```
fastapi==0.115.12, uvicorn==0.34.3     — API server
openai==1.82.1                          — Embeddings + LLM (gpt-4o-mini)
langchain==0.3.25                       — RAG pipeline
langchain-openai==0.3.19               — OpenAI connector
langchain-qdrant==0.2.0                — Qdrant vector store
qdrant-client==1.17.1                  — Qdrant client (query_points API)
pypdf==5.6.0                           — PDF text extraction
httpx==0.28.1, beautifulsoup4          — Web crawling
pandas>=2.0.0                          — DataFrame ops (JSON V1)
python-dotenv==1.1.0                   — Environment config
```

### Frontend
```
react@19, react-dom@19          — UI framework
react-toastify@11               — Toast notifications
vite@6                          — Build tool + hot reload
```

---

## 🔧 Configuration

### Chunking (in `indexing.py`)
| Parameter | Default |
|-----------|---------|
| Chunk Size | 1000 |
| Chunk Overlap | 200 |

### Relevance Threshold (`vector_search.py`)
```python
RELEVANCE_THRESHOLD = 0.4  # Cosine similarity minimum (0–1)
```

### JSON Qdrant Payload Indexes (created on upload)
- `metadata.price` — FLOAT (range filtering)
- `metadata.brand` — KEYWORD (exact match)
- `metadata.categoryName` — KEYWORD (exact match)
- `metadata.hasPromotions` — BOOL (flag filtering)

---

## 🚨 Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `'QdrantClient' has no attribute 'search'` | Old qdrant-client API | Use `query_points()` (already fixed in codebase) |
| `Index required but not found for "price"` | JSON indexed without payload indexes | Re-upload JSON to trigger new indexing |
| Context shows `N/A` for all product fields | Old JSON indexed as raw text chunks | Re-upload JSON with current `indexing.py` |
| Response marked IRRELEVANT by judge | LLM context too sparse or query too vague | Check backend logs for `combined_context` content |
| `The read operation timed out` | OpenAI call with too-large context | Top-5 limit is already applied; verified fixed |
| Duplicate search results | Same PDF uploaded multiple times | Old collection is auto-deleted on re-upload |
| Upload fails | File > 50MB or not a valid PDF/JSON | Check file size and format |
| Chat disabled after upload | Silent upload error | Check backend terminal for error logs |
| CORS errors in browser | Backend not running | Ensure `uvicorn` is running on port 8000 |

---

## 🔐 Security Notes

- `.env` is excluded from git via `.gitignore` — never commit it
- CORS currently allows all origins (`allow_origins=["*"]`) — restrict for production
- API keys only in `.env`, never hardcoded
- JSON and PDF upload endpoints validate file types

---

**Happy RAG Chatting! 🚀**