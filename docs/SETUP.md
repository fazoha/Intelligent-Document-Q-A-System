# Intelligent Document Q&A System — Setup Guide

A production-grade document question-answering system powered by NLP, OpenAI GPT-5-mini, and Upstash Vector DB. Upload PDFs, images, or Word documents and ask natural-language questions to get AI-generated answers with citations.

**Course:** COMP 4750 — Natural Language Processing  
**Status:** ✅ Phase 1 Complete | ✅ Phase 2 Complete

> **📝 Note**: This guide covers both Phase 1 and Phase 2 setup.  
> For Phase 2 technical details, see [PHASE2.md](./PHASE2.md)

> ⚠️ **IMPORTANT**: This system does **NOT preserve document history**. All uploaded documents and indexes are automatically cleared when the backend restarts. You must re-upload documents after each restart. This is intentional to maintain clean state.

---

## Features

- 📄 **Multi-format support**: PDF, PNG/JPG, DOCX
- 🧠 **Layout-aware parsing**: Preserves document structure (paragraphs, tables, headings)
- 🔍 **Semantic search**: Dense embeddings via OpenAI `text-embedding-3-large`
- 💬 **GPT-5-mini answers**: Context-aware responses with inline citations
- 🎨 **Modern UI**: Clean Next.js + Tailwind interface
- ⚡ **Fast & reliable**: Upstash serverless vector DB, no local infrastructure

---

## Architecture

```
Next.js Frontend (TypeScript + Tailwind)
    ↓ HTTP/JSON
FastAPI Backend (Python 3.11)
    ↓
┌─────────────────────────────────────┐
│  Unstructured.io  │  OpenAI API    │
│  (Parse docs)     │  (Embed + GPT) │
└─────────────────────────────────────┘
    ↓
Upstash Vector DB (Serverless)
```

---

## Prerequisites

### Required Software
- **Node.js** v18+ ([Download](https://nodejs.org/))
- **Python** 3.11+ ([Download](https://www.python.org/downloads/))
- **npm** (comes with Node.js)
- **pip** (comes with Python)

### Required API Keys
You'll need accounts and API keys from:

1. **OpenAI** ([platform.openai.com](https://platform.openai.com))
   - Create account, add payment method
   - Generate API key with access to `gpt-5-mini` and embeddings
   - Copy `OPENAI_API_KEY`

2. **Upstash Vector** ([console.upstash.com](https://console.upstash.com))
   - Create free account
   - Navigate to Vector tab → Create Index
   - Config: **Dense**, **1536 dimensions**, **Cosine** metric
   - Copy `UPSTASH_VECTOR_REST_URL` and `UPSTASH_VECTOR_REST_TOKEN`

3. **Unstructured.io** ([unstructured.io](https://unstructured.io))
   - Sign up for API access (free tier: 1,000 pages/month)
   - Copy `UNSTRUCTURED_API_KEY`

---

## Installation

### 1. Clone the Repository

```bash
cd /path/to/may-project/nextjs-fastapi
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Node.js Dependencies

```bash
npm install
```

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp env.example .env

# Edit .env with your actual API keys
nano .env  # or use any text editor
```

**Required variables in `.env`:**

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Upstash Vector
UPSTASH_VECTOR_REST_URL=https://xxxxx-xxxxx-xxxxx-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Unstructured.io
UNSTRUCTURED_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
UNSTRUCTURED_API_URL=https://api.unstructured.io/general/v0/general
```

Save and close the file.

### 5. Phase 2 Setup (Optional but Recommended)

Phase 2 adds hybrid retrieval (semantic + keywords), neural reranking, and multi-hop query planning.

**Pure NLP approach** - no external databases required!

#### 5a. Install Phase 2 Dependencies

```bash
cd backend
source venv/bin/activate  # if not already activated

# Install Phase 2 packages
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en_core_web_sm
```

#### 5b. Run Phase 2 Setup Script (Optional)

```bash
cd backend
python setup_phase2.py
```

This script verifies:
- ✅ Python version (3.10+)
- ✅ All dependencies installed
- ✅ spaCy model downloaded
- ✅ Environment variables set

#### 5c. Add Phase 2 Environment Variables

Add these to your `.env` file:

```bash
# Phase 2: Hybrid Retrieval Weights (Pure NLP: Dense + Keywords)
DENSE_WEIGHT=0.7        # Semantic similarity (OpenAI embeddings)
KEYWORD_WEIGHT=0.3      # Keyword overlap (YAKE extraction)

# Phase 2: Neural Reranking
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_TOP_K=20         # Candidates before reranking
FINAL_TOP_K=5           # Final results after reranking

# Phase 2: Query Planner (spaCy)
SPACY_MODEL=en_core_web_sm
ENABLE_MULTI_HOP=true

# Phase 2: YAKE Keyword Extraction
YAKE_MAX_KEYWORDS=10
YAKE_NGRAM_SIZE=3
```

**Note**: Phase 2 uses pure Python NLP components - no external databases required!

---

## Running the Application

### Option 1: Concurrent Mode (Recommended)

Run both servers with one command:

```bash
npm run dev
```

This starts:
- **FastAPI backend** on `http://localhost:8000`
- **Next.js frontend** on `http://localhost:3000`

### Option 2: Separate Terminals

**Terminal 1 (FastAPI):**
```bash
source venv/bin/activate  # if not already activated
npm run fastapi-dev
```

**Terminal 2 (Next.js):**
```bash
npm run next-dev
```

---

## Usage

1. **Open your browser** to [http://localhost:3000](http://localhost:3000)

2. **Upload a document**:
   - Drag & drop or click to browse
   - Supported: PDF, PNG, JPG, DOCX (max 10MB)
   - Wait for "✓ uploaded successfully" message

3. **Ask a question**:
   - Type your question in the text area
   - Click "Ask"
   - Wait 3-5 seconds for gpt-5-mini to generate an answer

4. **View citations**:
   - Citations appear as `[chunk_X]` tags in the answer
   - Click any citation to expand and see:
     - Original text from the document
     - Page number and bounding box
     - Block type (paragraph, table, etc.)

5. **Upload more documents** or click "Clear All" to reset

---

## API Endpoints

### Backend (FastAPI)

- `GET /api/py/` - Health check
- `POST /api/documents/upload` - Upload & index document
- `GET /api/documents` - List uploaded documents
- `DELETE /api/documents/{doc_id}` - Delete specific document
- `DELETE /api/documents/clear` - Clear all documents
- `POST /api/query` - Query documents & generate answer

**Interactive API Docs:** [http://localhost:8000/api/py/docs](http://localhost:8000/api/py/docs)

---

## Project Structure

```
nextjs-fastapi/
├── api/                      # FastAPI backend
│   ├── index.py              # Main app & routes registration
│   ├── models/               # Pydantic data models
│   │   ├── document.py       # Document & ChunkMetadata
│   │   └── query.py          # QueryRequest & QueryResponse
│   ├── routes/               # API endpoints
│   │   ├── documents.py      # Upload, list, delete
│   │   └── query.py          # Question answering
│   ├── services/             # Business logic
│   │   ├── document_parser.py     # Unstructured.io integration
│   │   ├── chunk_builder.py       # Layout-aware chunking
│   │   ├── embedding_service.py   # OpenAI embeddings
│   │   ├── vector_store.py        # Upstash Vector client
│   │   └── answer_generator.py    # gpt-5-mini answer generation
│   └── utils/                # Shared utilities
│       ├── config.py         # Environment config
│       └── logger.py         # Structured logging
├── app/                      # Next.js frontend
│   ├── page.tsx              # Main page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/               # React components
│   ├── UploadZone.tsx        # File upload UI
│   ├── QuestionInput.tsx     # Query input
│   ├── AnswerDisplay.tsx     # Answer & citations
│   ├── CitationCard.tsx      # Expandable citation
│   └── DocumentSidebar.tsx   # Document list
├── utils/
│   └── cn.ts                 # Tailwind class utility
├── requirements.txt          # Python dependencies
├── package.json              # Node.js dependencies
├── env.example               # Environment template
└── README.md                 # This file
```

---

## Troubleshooting

### "Configuration validation warning" on startup
- **Cause:** Missing or invalid API keys in `.env`
- **Fix:** Double-check your `.env` file has all required variables

### "Document parsing timed out"
- **Cause:** Large PDF or slow Unstructured.io API response
- **Fix:** Try a smaller document first; check internet connection

### "Failed to generate embedding"
- **Cause:** OpenAI API rate limit or invalid key
- **Fix:** Check API key, wait a minute, try again

### "No chunks found in vector store"
- **Cause:** No documents uploaded yet
- **Fix:** Upload at least one document before querying

### CORS errors in browser console
- **Cause:** Frontend trying to reach backend but CORS not configured
- **Fix:** Already configured in `api/index.py`; ensure backend is running on port 8000

### Python import errors
- **Cause:** Virtual environment not activated or dependencies not installed
- **Fix:**
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

---

## Performance Benchmarks (Phase 1)

| Metric | Target | Typical |
|--------|--------|---------|
| Upload & Index (10-page PDF) | < 15s | ~12s |
| Query → Answer | < 5s | ~3.5s |
| Embedding generation | < 500ms | ~350ms |
| Vector search (top-5) | < 200ms | ~150ms |

*Benchmarks on M1 Mac with 100Mbps internet.*

---

## Known Limitations (Phase 1)

- **No hybrid retrieval**: Only dense embeddings (keywords + reranking in Phase 2)
- **No reranking**: Simple cosine similarity (cross-encoder in Phase 2)
- **No query planning**: Single-hop queries only (multi-hop in Phase 2)
- **No confidence scoring**: No citation validation (Phase 3)
- **In-memory document store**: Documents reset on server restart (database in production)
- **No delete by doc_id**: Upstash Vector limitation (workaround in Phase 2)

---

## Next Steps (Phase 2)

1. Hybrid retrieval: Dense embeddings + YAKE keywords + Neural reranking
2. Cross-encoder reranking: `ms-marco-MiniLM-L-6-v2`
3. Query planner: spaCy dependency parsing, multi-hop orchestration
4. Better chunking: Smart table detection, section hierarchy
5. Persistent storage: PostgreSQL for documents, Redis for caching

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Modern React SPA |
| Backend | FastAPI, Python 3.11, Pydantic | Async API server |
| Document Parsing | Unstructured.io API | Extract text + layout |
| Embeddings | OpenAI `text-embedding-3-large` | 1536-dim vectors |
| LLM | OpenAI gpt-5-mini | Answer generation |
| Vector DB | Upstash Vector (serverless) | Semantic search |
| Utilities | tiktoken, python-dotenv | Tokenization, env config |

---

## License

MIT License - see LICENSE file

---

## Support

- **Course:** COMP 4750 - Natural Language Processing
- **Documentation:** See `docs/phase1-prd.md` for full spec
- **Issues:** Contact team or instructor

---

**Status:** ✅ Phase 1 Complete  
**Last Updated:** 2025-01-22
