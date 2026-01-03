# Intelligent Document Q&A System

**NLP-powered document question-answering with layout-aware parsing and GPT-5-mini**

A production-grade system for uploading documents (PDF, images, DOCX) and asking natural-language questions to receive AI-generated answers with precise citations.

**Course:** COMP 4750 — Natural Language Processing (Final Year)  
**Institution:** University  
**Status:** ✅ Phase 1 Complete | ✅ Phase 2 Complete | ✅ Phase 3 Complete

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

## Features

### Phase 1 (Core Functionality) ✅
- 📄 **Multi-format document support**: PDF, PNG/JPG, DOCX
- 🧠 **Layout-aware parsing**: Uses Unstructured.io to preserve document structure
- 🔍 **Semantic search**: Dense embeddings via OpenAI `text-embedding-3-large`
- 💬 **GPT-5-mini answers**: Context-aware responses with inline `[chunk_id]` citations
- 📊 **Citation transparency**: Every answer references specific document sections
- ⚡ **Serverless vector DB**: Upstash Vector (no local infrastructure needed)

### Phase 2 (Advanced NLP) ✅
- 🔀 **Hybrid retrieval**: Combines dense embeddings (semantic) + YAKE keywords (lexical)
- 🎯 **Neural reranking**: Cross-encoder model (`ms-marco-MiniLM-L-6-v2`) for precision
- 🧩 **Multi-hop reasoning**: spaCy-powered query planning for complex questions
- 📊 **Enhanced chunking**: Special handling for tables and section hierarchy
- ⚖️ **Weighted score fusion**: Configurable weights for semantic/keyword signals
- 🎓 **Pure NLP approach**: No external databases (Elasticsearch removed for simplicity)

### Phase 3 (Confidence & Evaluation) ✅
- 🎯 **Confidence scoring**: ROUGE-L citation overlap validation with visual indicators
- 🔄 **Extractive fallback**: DistilBERT span extraction for low-confidence answers
- 📊 **Answer validation**: Automatic detection of weak/unsupported answers
- 📈 **Evaluation harness**: Standard QA metrics (EM, F1, Recall@K, nDCG)
- 🧪 **Benchmarking**: Ablation study framework for systematic testing
- 🎨 **Enhanced UI**: Confidence meters and answer type indicators

### Technical Highlights
- **Layout metadata preservation**: Bounding boxes, page numbers, block types (paragraph/table/heading)
- **Intelligent chunking**: Up to 512 tokens per chunk with table isolation and section awareness
- **Pure NLP retrieval**: Dense embeddings → YAKE keywords → Score Fusion → Neural Reranking
- **Query understanding**: Dependency parsing and multi-hop detection with spaCy
- **Confidence validation**: ROUGE-L scoring with extractive QA fallback
- **Real-time processing**: Document → Parse → Chunk → Embed → Index in vector store
- **Modern UI**: Clean Next.js + Tailwind CSS interface with confidence indicators
- **API-first design**: FastAPI with auto-generated OpenAPI docs
- **Session-based operation**: No document history or persistence (fresh state on each restart)
- **Educational focus**: Pure NLP components, no external databases required

---

## Quick Start

### Prerequisites
- **Node.js** 18+ and **Python** 3.10+
- API keys from:
  - OpenAI (GPT-5-mini + embeddings)
  - Upstash Vector
  - Unstructured.io

### Installation

```bash
# 1. Clone and navigate to project
cd document-qa-system-main

# 2. Install Python dependencies (backend)
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Configure environment variables
cd ..
cp env.example .env
# Edit .env with your actual API keys

# 5. Install Node.js dependencies (frontend)
cd frontend
npm install
cd ..

# 6. Run backend (in one terminal)
cd backend
source venv/bin/activate
uvicorn index:app --reload --port 8000

# 7. Run frontend (in another terminal)
cd frontend
npm run dev
```

**Frontend:** http://localhost:3000  
**Backend API Docs:** http://localhost:8000/api/docs

⚠️ **IMPORTANT**: This system does **NOT preserve document history**. All uploaded documents and indexes are **automatically cleared** when the backend restarts. You must re-upload documents after each restart. This is intentional to maintain clean state and avoid stale data.

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

### ✅ Phase 1 (Complete)
- Core pipeline: upload → parse → chunk → embed → query → answer
- Layout-aware metadata preserved
- Basic dense retrieval (cosine similarity)
- GPT-5-mini answer generation with citations
- Modern Next.js + Tailwind UI

### ✅ Phase 2 (Complete)
- **Hybrid retrieval**: Dense embeddings (semantic) + YAKE keywords (lexical)
- **Cross-encoder reranking**: `ms-marco-MiniLM-L-6-v2` for semantic precision
- **Query planner**: Multi-hop reasoning with spaCy dependency parsing
- **Enhanced chunking**: Table isolation, section hierarchy tracking
- **Weighted score fusion**: Configurable semantic/keyword weights
- **Pure NLP approach**: No external databases - all Python-based NLP components

### ✅ Phase 3 (Complete)
- **Confidence scoring**: ROUGE-L citation overlap validation
- **Extractive fallback**: DistilBERT span extraction for low-confidence answers
- **Evaluation harness**: Standard QA metrics (EM, F1, Recall@K, nDCG)
- **Ablation framework**: Systematic benchmarking and comparison
- **Visual confidence**: UI indicators for answer quality

### 🔮 Phase 4 (Future)
- **Advanced query planning**: Coreference resolution for better multi-hop
- **Production deployment**: Vercel + Railway with caching
- **Model fine-tuning**: Domain-specific QA improvements
- **Active learning**: User feedback integration

---

## NLP Components (Academic Focus)

This project demonstrates multiple NLP techniques:

### Phase 1 Components
1. **Layout-aware document parsing** (Unstructured.io + LayoutParser concepts)
2. **Semantic chunking** with token counting (tiktoken)
3. **Dense embeddings** for retrieval (OpenAI text-embedding-3-large)
4. **Vector similarity search** (cosine distance in Upstash)
5. **Retrieval-Augmented Generation (RAG)** architecture
6. **Citation extraction** via regex pattern matching

### Phase 2 Components (Implemented)
7. **Keyword extraction** (YAKE unsupervised algorithm)
8. **Neural reranking** (cross-encoder transformer model)
9. **Dependency parsing** (spaCy) for query understanding
10. **Multi-hop reasoning** (clause detection and sequential retrieval)
11. **Hybrid score fusion** (weighted combination of semantic + keyword signals)

### Phase 3 Components (Implemented)
12. **Confidence scoring** (ROUGE-L citation overlap validation)
13. **Extractive QA** (DistilBERT span extraction)
14. **Evaluation metrics** (EM, F1, Recall@K, nDCG, MRR)
15. **Benchmarking framework** (ablation studies, comparison)

### Phase 4 Components (Planned)
- Coreference resolution
- Advanced query decomposition
- Domain-specific fine-tuning

---

## System Behavior & Limitations

### No Document History

⚠️ **This system operates in session-based mode**:

- **Documents are NOT saved**: All uploaded documents are cleared when the backend restarts
- **No history log**: There is no record of previously uploaded documents
- **Fresh state**: Each backend start provides a clean slate with no prior data
- **Re-upload required**: After restart, you must upload documents again to query them

**Why this design?**
- ✓ Avoids stale data and orphaned vectors in cloud storage
- ✓ Ensures consistency between in-memory state and vector databases
- ✓ Prevents confusion from test data accumulation
- ✓ Clean development and testing experience

**What this means for you:**
1. Upload your documents each session
2. Don't rely on documents persisting across restarts
3. Use sample documents or keep your files handy for re-upload
4. For production use, implement proper database persistence (future work)

---

## Documentation

- **`docs/NO_HISTORY_DESIGN.md`**: ⚠️ **READ FIRST** - Why documents don't persist (intentional design)
- **`docs/PHASE3.md`**: Complete Phase 3 technical documentation (confidence, evaluation)
- **`docs/PHASE2.md`**: Complete Phase 2 technical documentation (hybrid retrieval)
- **`docs/PHASE2_TESTING.md`**: Phase 2 testing procedures
- **`docs/SETUP.md`**: Detailed setup guide for all phases
- **`docs/phase1-prd.md`**: Comprehensive PRD with architecture, API specs, testing
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

**Last Updated:** November 27, 2025  
**Version:** 3.0.0 (Phase 3 Complete)
Date: Jan 3rd 2026
Next Steps: How to optimise this better?
