# Phase 3 Testing Guide

**Status:** ✅ Complete  
**Date:** November 27, 2025

---

## Quick Start Testing

### 1. Setup Verification

```bash
cd backend
python setup_phase3.py
```

This verifies:
- Python version (3.10+)
- Phase 3 dependencies installed
- Configuration loaded correctly
- Services can be imported
- Confidence scoring works

### 2. Start the System

```powershell
# Terminal 1: Backend
cd backend
.\venv\Scripts\activate
uvicorn index:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 3. Install New Dependencies (if needed)

```bash
cd backend
.\venv\Scripts\activate
pip install rouge-score transformers datasets
```

---

## Manual Testing Procedures

### Test 1: Confidence Scoring Display

**Steps:**
1. Upload a document (PDF or sample)
2. Ask a question that should be well-supported by the document
3. Check the answer display

**Expected Results:**
- Confidence percentage displayed (e.g., "78%")
- Color-coded indicator:
  - 🟢 Green = High (≥70%)
  - 🟡 Yellow = Medium (40-70%)
  - 🔴 Red = Low (<40%)
- Tooltip shows confidence details

**Sample Queries for Testing:**
- "What is the main topic of this document?" → Should show high confidence
- "What specific numbers are mentioned?" → Should show medium-high confidence
- "What is not mentioned in this document?" → Should show low confidence

---

### Test 2: Extractive Fallback

**Steps:**
1. Upload a document
2. Ask a question that might produce low-confidence generative answer
3. Observe if extractive fallback triggers

**Expected Results:**
- If confidence < 0.4, system tries extractive QA
- Answer type badge shows "Direct Quote" for extractive answers
- Header changes from "AI Synthesis" to "Extracted Answer"

**To Force Extractive Fallback:**
- Ask very specific factoid questions
- Ask about specific numbers or dates
- Questions where direct quotes are more appropriate

---

### Test 3: API Response Validation

**Using curl/PowerShell:**

```powershell
$body = @{
    query = "What is this document about?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Expected Response Fields:**
```json
{
  "answer": "...",
  "citations": [...],
  "query_time_ms": 2341,
  "retrieved_chunks": 5,
  "confidence_score": 0.78,
  "confidence_level": "high",
  "answer_type": "generative",
  "extractive_span": null
}
```

---

### Test 4: Evaluation Harness

**Run Sample Evaluation:**

```bash
cd backend
python evaluate_phase3.py --dataset sample
```

**Expected Output:**
- Loads 10 sample examples
- Computes metrics (EM, F1, Recall@K, nDCG)
- Displays summary results

**Run Ablation Study:**

```bash
python evaluate_phase3.py --ablation
```

---

### Test 5: Unit Tests

**Run Confidence Tests:**

```bash
cd backend
pytest tests/test_confidence_service.py -v
```

**Run Metrics Tests:**

```bash
pytest tests/test_evaluation_metrics.py -v
```

**Run All Tests:**

```bash
pytest tests/ -v
```

---

## Verification Checklist

### Backend
- [ ] `setup_phase3.py` passes all checks
- [ ] No import errors in services
- [ ] API returns confidence_score field
- [ ] API returns answer_type field
- [ ] Extractive fallback triggers on low confidence

### Frontend
- [ ] Confidence indicator displays correctly
- [ ] Color coding works (green/yellow/red)
- [ ] Tooltip shows confidence details
- [ ] "Direct Quote" badge appears for extractive answers
- [ ] Header changes for extractive answers

### Evaluation
- [ ] Sample evaluation runs successfully
- [ ] Metrics are computed correctly
- [ ] Ablation study generates report
- [ ] Results can be saved to file

---

## Troubleshooting

### "Module not found" Errors

```bash
pip install rouge-score transformers datasets
```

### "Model download failed"

```python
# Manually download model
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
AutoTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")
AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")
```

### Confidence Always Low

1. Check that GPT is citing chunks properly (`[chunk_X]` format)
2. Verify citations contain relevant text
3. Check the answer matches citation content

### Extractive Never Triggers

1. Check `CONFIDENCE_THRESHOLD` in config (default: 0.4)
2. Verify `ENABLE_EXTRACTIVE_FALLBACK=true`
3. Test with questions that produce poor citations

### Frontend Not Showing Confidence

1. Verify backend returns confidence fields
2. Check browser console for errors
3. Ensure frontend is using latest code

---

## Performance Benchmarks

### Expected Latencies

| Component | Time |
|-----------|------|
| Confidence scoring | 10-30ms |
| Extractive fallback | 100-200ms |
| Total query (Phase 3) | +50-200ms vs Phase 2 |

### Memory Usage

| Model | Memory |
|-------|--------|
| DistilBERT | ~500MB (loaded on first use) |
| Cross-encoder | ~200MB (from Phase 2) |

---

## Test Data Files

### Sample Dataset Location

```
backend/evaluation/datasets/sample_dataset.py
```

### Custom Test Dataset Format

```json
[
  {
    "id": "1",
    "question": "What is X?",
    "answer": "X is Y",
    "relevant_chunks": ["chunk_1"]
  }
]
```

**Usage:**

```bash
python evaluate_phase3.py --dataset my_data.json
```

---

## Success Criteria

Phase 3 testing is complete when:

✅ All unit tests pass  
✅ Confidence scoring displays correctly  
✅ Extractive fallback works when triggered  
✅ Evaluation harness runs without errors  
✅ API returns all new fields  
✅ Frontend displays all indicators  
✅ Performance is acceptable (<500ms additional latency)


