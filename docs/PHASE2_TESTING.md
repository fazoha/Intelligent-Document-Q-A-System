# Phase 2 Testing Guide

Quick guide to verify Phase 2 features are working correctly.

---

## Prerequisites

1. Backend running: `uvicorn index:app --reload --port 8000`
2. Frontend running: `npm run dev` (in frontend folder)
3. Elasticsearch running: `docker-compose up -d` (optional but recommended)

---

## Test 1: Verify Services

### Check Backend API

```bash
curl http://localhost:8000/api/docs
```

**Expected**: OpenAPI documentation page loads

### Check Elasticsearch (if running)

```bash
curl http://localhost:9200
```

**Expected**: JSON response with Elasticsearch version

---

## Test 2: Document Upload with Dual Indexing

### Upload a Sample Document

**Via UI**:
1. Go to http://localhost:3000
2. Click "Sample Documents"
3. Select "employee-benefits-handbook.pdf"
4. Click "Load Sample"

**Via API**:
```bash
curl -X POST http://localhost:8000/api/documents/samples/load \
  -H "Content-Type: application/json" \
  -d '{"filename": "employee-benefits-handbook.pdf"}'
```

### Verify Indexing

Check backend logs for:
```
✅ Successfully indexed X chunks in Elasticsearch
```

If Elasticsearch is unavailable, you'll see:
```
⚠️  BM25 indexing failed or unavailable - dense retrieval only
```

---

## Test 3: Simple Query (Single-hop)

### Test Query

**Via UI**:
- Enter: "What are the vacation policies?"
- Click "Ask"

**Via API**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the vacation policies?"}'
```

### Verify Phase 2 Features

Check backend logs for:
```
✅ Query analysis: multi_hop=False, type=what
✅ Dense retrieval: X chunks
✅ BM25 retrieval: X results
✅ Merged results: X unique chunks
✅ Reranking complete: X final results
```

**Expected Response**:
- Answer with relevant content
- Citations with `[chunk_X]` references
- `query_time_ms`: 1500-3000ms
- `retrieved_chunks`: 5

---

## Test 4: Multi-hop Query

### Test Complex Query

**Via UI**:
- Enter: "What are the vacation days and who approves them?"

**Via API**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the vacation days and who approves them?"}'
```

### Verify Multi-hop Detection

Check backend logs for:
```
✅ Query analysis: multi_hop=True
✅ Multi-hop retrieval with 2 sub-queries
✅ Processing sub-query 1/2: What are the vacation days?
✅ Processing sub-query 2/2: Who approves them?
```

**Expected Behavior**:
- System processes each sub-query separately
- Combines results
- Generates unified answer
- More chunks may be retrieved than single-hop

---

## Test 5: Hybrid Retrieval Verification

### Test with Exact Terms (Benefits BM25)

**Query**: "401k matching contribution percentage"

**Expected**:
- BM25 should score highly (exact term matching)
- Check logs for high `bm25_score` values

### Test with Conceptual Query (Benefits Dense)

**Query**: "retirement savings plan details"

**Expected**:
- Dense retrieval should score highly (semantic similarity)
- Check logs for high `dense_score` values

### Test with Keywords (Benefits YAKE)

**Query**: "PTO accrual sick leave"

**Expected**:
- Keyword matching should contribute
- Check logs for `keyword_score` values

---

## Test 6: Table Handling

### Upload Document with Tables

Use "product-requirements-spec.pdf" or "clinical-trial-brief.pdf"

### Query Table Content

**Query**: "What are the technical specifications?" or "What are the trial results?"

**Expected**:
- System retrieves table chunks
- Check logs for `block_type=table`
- Answer includes structured data from tables

---

## Test 7: Reranking Verification

### Compare Results

**Without Reranking** (temporarily disable):
1. Edit `backend/utils/config.py`
2. Set `FINAL_TOP_K = RERANK_TOP_K` (bypass reranking)
3. Run query

**With Reranking** (default):
1. Restore config
2. Run same query

**Expected**:
- Reranked results should be more relevant
- Check logs for reranker scores

---

## Test 8: Elasticsearch Fallback

### Test Without Elasticsearch

1. Stop Elasticsearch: `docker-compose down`
2. Upload a document
3. Run a query

**Expected Behavior**:
- System logs: "BM25 service unavailable"
- Falls back to dense retrieval only
- Queries still work (Phase 1 mode)
- No errors

---

## Test 9: Load Testing

### Multiple Documents

Upload 3-5 sample documents:
- employee-benefits-handbook.pdf
- product-requirements-spec.pdf
- clinical-trial-brief.pdf
- enterprise-risk-assessment.pdf
- security-incident-report.pdf

### Cross-Document Query

**Query**: "What security measures are mentioned across all documents?"

**Expected**:
- Retrieves chunks from multiple documents
- Citations show different doc_names
- Hybrid retrieval handles multi-document corpus

---

## Test 10: Performance Check

### Measure Query Time

Run multiple queries and check `query_time_ms`:

**Expected Ranges**:
- Simple queries: 1500-2500ms
- Multi-hop queries: 2000-4000ms
- With Elasticsearch: +200-500ms (retrieval)
- With Reranking: +100-300ms

**Performance Tips**:
- First query may be slower (model loading)
- Subsequent queries should be faster (caching)
- Reranking time scales with candidates

---

## Troubleshooting

### Issue: "spaCy model not found"

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Issue: "Elasticsearch connection refused"

**Solution**:
```bash
# Start Elasticsearch
docker-compose up -d

# Verify
curl http://localhost:9200
```

### Issue: "Cross-encoder OOM"

**Solution**: Reduce reranking candidates in `.env`:
```bash
RERANK_TOP_K=10  # Down from 20
```

### Issue: Slow queries

**Solutions**:
1. Reduce `RERANK_TOP_K`
2. Disable multi-hop: `ENABLE_MULTI_HOP=false`
3. Adjust retrieval weights

---

## Success Criteria

✅ **Phase 2 is working correctly if**:

1. Documents upload and index in both Vector DB and Elasticsearch
2. Logs show hybrid retrieval (dense + BM25 + keywords)
3. Reranking processes top candidates
4. Multi-hop queries are detected and processed
5. Answers are relevant and cited
6. System falls back gracefully without Elasticsearch
7. Query times are reasonable (< 5s)
8. Table content is properly extracted
9. Cross-document queries work

---

## Verification Checklist

- [ ] Setup script passes all checks
- [ ] Document uploads successfully
- [ ] Elasticsearch receives chunks
- [ ] Simple queries return answers
- [ ] Multi-hop queries are detected
- [ ] Hybrid retrieval combines signals
- [ ] Reranking improves results
- [ ] Table content is retrieved
- [ ] Fallback works without ES
- [ ] Performance is acceptable

---

## Next Steps

After verifying Phase 2:

1. **Optimize weights**: Adjust `DENSE_WEIGHT`, `BM25_WEIGHT`, `KEYWORD_WEIGHT`
2. **Fine-tune reranking**: Experiment with `RERANK_TOP_K`
3. **Test edge cases**: Very long queries, short queries, multiple documents
4. **Benchmark**: Compare Phase 1 vs Phase 2 retrieval quality
5. **Plan Phase 3**: Confidence scoring, evaluation harness

---

**Testing Complete!** 🎉

If all tests pass, Phase 2 is successfully implemented and ready for use.

