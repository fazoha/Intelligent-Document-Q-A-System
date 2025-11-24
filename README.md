# Intelligent Document Q&A System

**NLP-powered document question-answering with layout-aware parsing and GPT-5-mini**

A production-grade system for uploading documents (PDF, images, DOCX) and asking natural-language questions to receive AI-generated answers with precise citations.

**Course:** COMP 4750 — Natural Language Processing (Final Year)  
**Institution:** University  
**Status:** ✅ Phase 1 Complete

---

## Project Structure

```
may-project/
├── backend/                       # FastAPI backend (Python)
│   ├── models/                    # Pydantic data models
│   ├── routes/                    # API endpoints
│   ├── services/                  # Business logic (parsing, embedding, etc.)
│   ├── utils/                     # Config & logging
│   ├── index.py                   # FastAPI app entry point
│   └── requirements.txt           # Python dependencies
├── frontend/                      # Next.js frontend (TypeScript + React)
│   ├── src/
│   │   ├── app/                   # Next.js 14 pages
│   │   ├── components/            # React components
│   │   └── utils/                 # Frontend utilities
│   ├── public/                    # Static assets
│   ├── package.json               # Node.js dependencies
│   └── tsconfig.json              # TypeScript config
├── docs/                          # Documentation
│   ├── phase1-prd.md              # Comprehensive PRD
│   ├── SETUP.md                   # Detailed setup guide
│   └── TESTING.md                 # Testing procedures
├── project-proposal.md            # Final project proposal
├── env.example                    # Environment variables template
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

---

## Features (Phase 1)

### Core Functionality
- 📄 **Multi-format document support**: PDF, PNG/JPG, DOCX
- 🧠 **Layout-aware parsing**: Uses Unstructured.io to preserve document structure
- 🔍 **Semantic search**: Dense embeddings via OpenAI `text-embedding-3-large`
- 💬 **GPT-5-mini answers**: Context-aware responses with inline `[chunk_id]` citations
- 📊 **Citation transparency**: Every answer references specific document sections
- ⚡ **Serverless vector DB**: Upstash Vector (no local infrastructure needed)

### Technical Highlights
- **Layout metadata preservation**: Bounding boxes, page numbers, block types (paragraph/table/heading)
- **Intelligent chunking**: Up to 512 tokens per chunk with section awareness
- **Real-time processing**: Document → Parse → Chunk → Embed → Index in ~10-15 seconds
- **Modern UI**: Clean Next.js + Tailwind CSS interface
- **API-first design**: FastAPI with auto-generated OpenAPI docs

---

## Quick Start

### Prerequisites
- **Node.js** 18+ and **Python** 3.11+
- API keys from:
  - OpenAI (GPT-5-mini + embeddings)
  - Upstash Vector
  - Unstructured.io

### Installation

```bash
# 1. Install Python dependencies (backend)
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 2. Install Node.js dependencies (frontend)
cd frontend
npm install
cd ..

# 3. Configure environment variables
cp env.example .env
# Edit .env with your actual API keys

# 4. Run backend (in one terminal)
cd backend
source venv/bin/activate
uvicorn index:app --reload --port 8000

# 5. Run frontend (in another terminal)
cd frontend
npm run dev
```

**Frontend:** http://localhost:3000  
**Backend API Docs:** http://localhost:8000/api/docs

📖 **Detailed setup guide:** See `docs/SETUP.md`

---

## Architecture

```
┌─────────────────────┐
│  Next.js Frontend   │  ← User uploads docs, asks questions
│  (TypeScript + TW)  │
└──────────┬──────────┘
           │ HTTP/JSON
┌──────────▼──────────┐
│   FastAPI Backend   │  ← Orchestrates NLP pipeline
│   (Python 3.11)     │
└──────────┬──────────┘
           │
    ┌──────┴──────┬───────────────┬────────────┐
    │             │               │            │
┌───▼────┐  ┌────▼─────┐  ┌──────▼─────┐  ┌──▼──────┐
│Unstruct│  │  OpenAI  │  │  Upstash   │  │ Logging │
│ured.io │  │Embeddings│  │   Vector   │  │ & Conf  │
│        │  │  + GPT-5-mini │  │     DB     │  │         │
└────────┘  └──────────┘  └────────────┘  └─────────┘
```

### Data Flow
1. **Upload**: User drops PDF → FastAPI receives file
2. **Parse**: Unstructured.io extracts text + layout (bboxes, pages, types)
3. **Chunk**: Smart chunking preserves sections, max 512 tokens
4. **Embed**: OpenAI generates 1536-dim vectors per chunk
5. **Index**: Upstash Vector stores embeddings + metadata
6. **Query**: User asks question → embed query → cosine search → top-5 chunks
7. **Generate**: GPT-5-mini composes answer citing `[chunk_X]` IDs
8. **Display**: UI shows answer with expandable citations

---

## Phase Roadmap

### ✅ Phase 1 (Current)
- Core pipeline: upload → parse → chunk → embed → query → answer
- Layout-aware metadata preserved
- Basic dense retrieval (cosine similarity)
- GPT-5-mini answer generation with citations

### 🔄 Phase 2 (Planned)
- **Hybrid retrieval**: BM25 (Elasticsearch) + YAKE keywords
- **Cross-encoder reranking**: `ms-marco-MiniLM-L-6-v2`
- **Query planner**: Multi-hop reasoning with spaCy
- **Better chunking**: Table extraction, section hierarchy

### 🔮 Phase 3 (Future)
- **Confidence scoring**: ROUGE-L citation overlap validation
- **Extractive fallback**: Direct span highlighting
- **Evaluation harness**: Automated benchmarking
- **Production deployment**: Vercel + Railway

---

## NLP Components (Academic Focus)

This project demonstrates:

1. **Layout-aware document parsing** (Unstructured.io + LayoutParser concepts)
2. **Semantic chunking** with token counting (tiktoken)
3. **Dense embeddings** for retrieval (OpenAI text-embedding-3-large)
4. **Vector similarity search** (cosine distance in Upstash)
5. **Retrieval-Augmented Generation (RAG)** architecture
6. **Citation extraction** via regex pattern matching

**Future phases add:**
- Lexical retrieval (BM25, TF-IDF)
- Neural reranking (cross-encoders)
- Dependency parsing (spaCy) for query understanding
- Coreference resolution for multi-hop queries

---

## Documentation

- **`docs/phase1-prd.md`**: Comprehensive PRD with architecture, API specs, testing
- **`nextjs-fastapi/README.md`**: Detailed installation and usage guide
- **`nextjs-fastapi/TESTING.md`**: Manual testing procedures
- **`project-proposal.md`**: Academic project proposal

---

## License

Academic project for COMP 4750. All rights reserved.

---

## Support & Contact

- **Issues**: [Create GitHub issue or contact team]
- **Course**: COMP 4750 - Natural Language Processing
- **Semester**: [Add semester/year]

---

**Last Updated:** November 22, 2025  
**Version:** 1.0.0 (Phase 1 Complete)
