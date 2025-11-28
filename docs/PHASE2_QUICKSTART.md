# Phase 2 Quick Start Guide

**5-Minute Setup** for Intelligent Document Q&A System Phase 2

---

## Prerequisites Check

```bash
# Python 3.10+
python --version

# Node.js 18+
node --version
```

**Note:** Docker/Elasticsearch NOT required - this is a pure Python NLP approach!

---

## Setup (5 minutes)

### 1. Install Python Dependencies (2 minutes)

**Windows PowerShell:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Linux/Mac:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment (1 minute)

**Windows PowerShell:**
```powershell
cd ..
Copy-Item env.example .env
```

**Linux/Mac:**
```bash
cd ..
cp env.example .env
```

**Edit `.env`** with your API keys (already filled in example):
- `OPENAI_API_KEY`
- `UPSTASH_VECTOR_REST_URL`
- `UPSTASH_VECTOR_REST_TOKEN`
- `UNSTRUCTURED_API_KEY`

### 3. Install Frontend Dependencies (1 minute)

```bash
cd ../frontend
npm install
```

---

## Run (2 commands)

### Terminal 1: Backend

**Windows PowerShell:**
```powershell
cd backend
.\venv\Scripts\activate
uvicorn index:app --reload --port 8000
```

**Linux/Mac:**
```bash
cd backend
source venv/bin/activate
uvicorn index:app --reload --port 8000
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

---

## Test (30 seconds)

⚠️ **IMPORTANT**: Documents are NOT saved between backend restarts. You must upload documents after every backend start.

1. Open http://localhost:3000
2. Click "Sample Documents" → Select any PDF → "Load Sample"
3. Wait for "Document indexed successfully"
4. Ask a question: "What is this document about?"
5. See answer with citations!

**Note**: If you restart the backend, repeat steps 2-5.

---

## Phase 2 Features in Action

### Test Multi-hop Query

Try: "What are the vacation policies and who approves them?"

**What happens**:
- Query planner splits into 2 sub-queries
- Each sub-query runs hybrid retrieval
- Results are combined and reranked
- GPT-5-mini generates unified answer

**Check logs** to see multi-hop in action!

### Test Hybrid Retrieval

Try these queries to see different retrieval strategies:

1. **Dense (semantic)**: "retirement savings options"
2. **Keywords (YAKE)**: "401k matching percentage"
3. **Combined**: "PTO sick leave accrual"

Hybrid retrieval combines semantic understanding with keyword extraction!

---

## Troubleshooting

### "My documents disappeared!"

**This is normal behavior**. The system clears all documents when the backend restarts.

**Solution**: Re-upload your documents. This is intentional, not a bug.

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Port already in use
```bash
# Change ports in .env:
FASTAPI_PORT=8001
# Update frontend next.config.js accordingly
```

### Backend restart clears data

**Expected behavior**: Check backend logs on startup:
```
⚠️ STARTUP: Clearing vector stores
✓ System ready with clean state
```

This means the system is working correctly.

---

## Quick Commands

**Windows PowerShell:**
```powershell
# Backend
cd backend; .\venv\Scripts\activate; uvicorn index:app --reload

# Frontend
cd frontend; npm run dev
```

**Linux/Mac:**
```bash
# Backend
cd backend && source venv/bin/activate && uvicorn index:app --reload

# Frontend
cd frontend && npm run dev
```

---

## What's Different in Phase 2?

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| Retrieval | Dense only | Dense + YAKE Keywords |
| Accuracy | ~60% | ~75-80% |
| Tables | Poor | Excellent |
| Multi-hop | No | Yes (spaCy) |
| Reranking | No | Yes (cross-encoder) |
| Dependencies | Minimal | Pure Python NLP |

---

## Next Steps

1. Upload your own documents
2. Try different query types
3. Experiment with retrieval weights in `.env`
4. Read full docs: `docs/PHASE2.md`
5. Run test suite: `docs/PHASE2_TESTING.md`

---

## File Structure

```
document-qa-system-main/
├── backend/
│   ├── services/
│   │   ├── keyword_service.py       ← YAKE keywords
│   │   ├── reranker_service.py      ← Cross-encoder
│   │   ├── hybrid_retriever.py      ← Orchestrator
│   │   └── query_planner.py         ← Multi-hop
│   ├── setup_phase2.py              ← Setup script
│   └── requirements.txt             ← Dependencies
├── docs/
│   ├── PHASE2.md                    ← Full docs
│   └── PHASE2_TESTING.md            ← Testing guide
└── README.md                        ← Main readme
```

---

## Configuration Tuning

Edit `.env` to tune retrieval:

```bash
# More semantic (conceptual queries)
DENSE_WEIGHT=0.8
KEYWORD_WEIGHT=0.2

# More keyword-focused (exact terms)
DENSE_WEIGHT=0.5
KEYWORD_WEIGHT=0.5

# Faster (fewer candidates)
RERANK_TOP_K=10
FINAL_TOP_K=3
```

---

## Support

- **Documentation**: See `docs/` folder
- **Issues**: Check backend logs
- **Testing**: Run `python setup_phase2.py`

---

**You're all set!** 🎉

Phase 2 is ready to use. Enjoy hybrid retrieval, multi-hop reasoning, and improved accuracy!

