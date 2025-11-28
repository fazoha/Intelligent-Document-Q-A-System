# System Design: No Document History

**Version:** 2.0.0  
**Status:** ✅ Implemented  
**Date:** November 24, 2025

---

## Overview

This Intelligent Document Q&A System is designed to **NOT preserve document history** across backend restarts. This document explains this design decision and its implications.

---

## How It Works

### Automatic Cleanup on Startup

When the backend starts (`uvicorn index:app`), it automatically:

1. **Detects fresh start**: Checks if in-memory `document_store` is empty
2. **Clears Upstash Vector DB**: Removes all document embeddings
3. **Logs warnings**: Clearly indicates cleanup is happening

### What You'll See

```bash
$ uvicorn index:app --reload --port 8000

======================================================================
STARTUP: document_store is empty - clearing vector store
All previous documents will be removed from vector database
This is intentional behavior to maintain clean state
======================================================================
✓ Upstash Vector DB cleared
======================================================================
STARTUP COMPLETE: System ready with clean state
Pure NLP approach: Dense embeddings + YAKE keywords + Neural reranking
Please upload documents to begin querying
======================================================================
```

---

## User Impact

### What This Means for You

| Action | Result |
|--------|--------|
| Backend starts | All previous documents deleted |
| Code changes + restart | Must re-upload documents |
| Server crashes | All documents lost |
| Stop/start backend | Fresh slate |
| Deploy new version | Previous data cleared |

### Workflow

**Normal usage pattern:**

```
1. Start backend
   └─> System clears old data

2. Upload documents (via UI or API)
   └─> Documents indexed in current session

3. Query documents
   └─> Works normally

4. If backend restarts (code change, crash, etc.)
   └─> Go back to step 2 (re-upload)
```

---

## Why This Design?

### Advantages

1. **Clean State**
   - No stale data from previous sessions
   - No confusion about what's indexed
   - Clear mental model: restart = fresh start

2. **Consistency**
   - In-memory state always matches vector stores
   - No orphaned embeddings in cloud storage
   - No sync issues between storage layers

3. **Cost Efficiency**
   - No accumulation of test data in Upstash (paid service)
   - No forgotten documents consuming storage
   - Easy to track resource usage

4. **Development Friendly**
   - Quick iteration without cleanup step
   - No "why is old data still here?" confusion
   - Easy to reproduce issues with known state

5. **Simplicity**
   - No complex sync logic needed
   - No database for document metadata
   - Fewer failure modes

### Trade-offs

1. **Must Re-upload Documents**
   - After every restart
   - Can be tedious during development
   - Mitigated by sample documents feature

2. **Not Production-Ready**
   - Users would lose data on server maintenance
   - Not acceptable for real-world deployment
   - Would need database persistence for production

3. **No Session Recovery**
   - Can't resume previous work
   - No document history or logs
   - Fresh start every time

---

## Use Cases

### ✅ Good For

- **Course projects** (like this COMP 4750 project)
- **Development and testing** (quick iterations)
- **Demo sessions** (clean slate between demos)
- **Research experiments** (controlled starting conditions)
- **Short-lived sessions** (upload once, query many times)

### ❌ Not Good For

- **Production deployment** (users expect persistence)
- **Long-running servers** (maintenance would lose data)
- **Document libraries** (need permanent storage)
- **Collaborative work** (multiple users sharing documents)
- **Historical analysis** (need to track previous uploads)

---

## Alternatives Considered

### Option A: Database Persistence (Production)

**Implementation**: Add PostgreSQL/SQLite for document metadata

**Pros:**
- Full persistence across restarts
- Production-ready
- User-friendly

**Cons:**
- More complex setup
- Additional dependency
- More code to maintain

**Status:** Not implemented (out of scope for Phase 2)

### Option B: Startup Sync (Hybrid)

**Implementation**: Query vector store on startup, rebuild document list

**Pros:**
- Documents persist
- No separate database needed

**Cons:**
- Slow startup (queries cloud services)
- Incomplete metadata recovery
- Sync can fail
- Upstash doesn't support "list all" easily

**Status:** Not implemented (too complex for benefit)

### Option C: Clear on Startup (Current) ✅

**Implementation**: Automatically clear vector stores if `document_store` is empty

**Pros:**
- Simple and reliable
- Fast startup
- Always consistent state
- Clean development experience

**Cons:**
- Data loss on restart
- Not production-ready
- Must re-upload frequently

**Status:** ✅ **IMPLEMENTED**

---

## Implementation Details

### Code Location

**Primary implementation**: `backend/index.py`

```python
@app.on_event("startup")
async def clear_vector_stores_on_startup():
    """Clear all vector stores on startup to ensure clean state."""
    
    if len(document_store) == 0:
        # Clear Upstash Vector DB
        vector_store = UpstashVectorStore()
        vector_store.reset()
        
        # Note: Elasticsearch/BM25 removed - using pure NLP approach
```

### Testing the Behavior

1. **Upload a document**
2. **Restart backend**: `Ctrl+C` then `uvicorn index:app --reload`
3. **Check logs**: Should see cleanup warnings
4. **Try to query**: Should return "no documents indexed"
5. **Re-upload**: Works normally again

---

## FAQ

### Q: Is this a bug?

**A:** No, this is intentional behavior by design.

### Q: Can I disable the auto-clear?

**A:** Not recommended. It would cause state inconsistency issues. If you need persistence, implement Option A (database).

### Q: My documents disappeared!

**A:** This is expected if the backend restarted. Re-upload your documents.

### Q: How do I preserve documents?

**A:** For production use, implement database persistence (Option A). For development, keep sample documents ready to reload.

### Q: Will this change in Phase 3?

**A:** Phase 3 focuses on confidence scoring and evaluation. Persistence is a separate production enhancement not part of the academic project phases.

### Q: What about the sample documents?

**A:** Sample documents are files in `sample-docs/` folder. They're not "uploaded" until you load them via UI/API. They're always available to reload.

---

## For Developers

### Modifying the Behavior

If you want to change this behavior:

1. **To disable auto-clear** (not recommended):
   ```python
   # Comment out the startup event in backend/index.py
   # @app.on_event("startup")
   # async def clear_vector_stores_on_startup():
   #     ...
   ```

2. **To add persistence**:
   - Install database (PostgreSQL/SQLite)
   - Create `documents` table
   - Modify `document_store` to use database
   - Update upload/delete endpoints
   - Add sync logic on startup

3. **To implement hybrid mode**:
   - Add `DEVELOPMENT_MODE` env variable
   - Clear only if `DEVELOPMENT_MODE=true`
   - Use database in production mode

---

## Summary

✅ **This system intentionally does NOT save documents across restarts**

**Key takeaways:**
1. Backend restart = all documents deleted
2. Must re-upload documents each session
3. This is by design, not a bug
4. Sample documents make this painless
5. For production, implement database persistence

**User expectations:**
- Upload documents at start of each session
- Don't rely on document history
- Use sample documents for quick testing
- Understand this is development/academic setup

---

**Last Updated:** November 24, 2025  
**Implementation Status:** ✅ Complete  
**Production Status:** ⚠️ Not production-ready (by design)

