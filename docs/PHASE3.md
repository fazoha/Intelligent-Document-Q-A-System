# Phase 3 Documentation — Confidence Scoring & Evaluation

**Version:** 3.0.0  
**Status:** ✅ Complete  
**Date:** November 27, 2025

---

## Overview

Phase 3 adds confidence scoring, extractive fallback, and evaluation capabilities to the Intelligent Document Q&A System. These features enhance answer quality validation, provide alternative QA approaches for low-confidence scenarios, and enable systematic benchmarking.

---

## Architecture Changes

### Phase 2 (Baseline)
```
Query → Query Planner → Hybrid Retrieval → Reranking → GPT-5-mini → Answer
```

### Phase 3 (Enhanced)
```
Query → Query Planner → Hybrid Retrieval → Reranking
                                            ↓
                                    GPT-5-mini Answer
                                            ↓
                              Confidence Scoring (ROUGE-L)
                                            ↓
                               ┌─── High Confidence ───┐
                               │                       │
                               ↓                       ↓
                        Return Answer           Low Confidence
                                                      ↓
                                            Extractive Fallback
                                              (DistilBERT)
                                                      ↓
                                             Compare Scores
                                                      ↓
                                            Return Best Answer
```

---

## New Components

### 1. Confidence Scorer (`confidence_service.py`)

**Purpose**: Validates that generated answers are supported by cited chunks.

**Key Features**:
- ROUGE-L (Longest Common Subsequence) scoring
- Token overlap calculation
- Sentence-level confidence analysis
- Human-readable confidence levels (high/medium/low)

**Algorithm**:
```python
confidence = 0.7 * rouge_l + 0.3 * token_overlap
```

**Confidence Levels**:
- **High** (≥0.7): Answer is well-supported by citations
- **Medium** (0.4-0.7): Answer is partially supported
- **Low** (<0.4): Answer may not be fully supported

**Configuration**:
```python
CONFIDENCE_THRESHOLD=0.4  # Triggers extractive fallback below this
```

**Example**:
```python
from services import ConfidenceScorer

scorer = ConfidenceScorer()

# Compute confidence
score = scorer.compute_confidence_score(
    answer="The revenue grew by 25%.",
    citations=[Citation(text="Revenue increased 25% in Q4...")]
)
# Output: 0.823 (high confidence)

level = scorer.get_confidence_level(score)
# Output: "high"
```

---

### 2. Extractive QA Service (`extractive_qa_service.py`)

**Purpose**: Direct span extraction from source documents using DistilBERT.

**Key Features**:
- Uses `distilbert-base-uncased-distilled-squad` model
- Extracts answer spans with character positions
- Provides confidence scores for extracted answers
- Lazy model loading to avoid startup delay

**When Used**:
- Generative answer confidence < threshold (default: 0.4)
- Extractive fallback is enabled
- Extractive score > generative score

**Configuration**:
```python
ENABLE_EXTRACTIVE_FALLBACK=true
EXTRACTIVE_MODEL=distilbert-base-uncased-distilled-squad
```

**Example**:
```python
from services import ExtractiveQAService

extractor = ExtractiveQAService()

answer, score, span = extractor.extract_answer(
    question="What is the confidence threshold?",
    chunks=[ChunkMetadata(text="The default threshold is 0.4...")]
)
# Output: ("0.4", 0.92, {"start_char": 25, "end_char": 28})
```

---

### 3. Evaluation Harness (`evaluation/`)

**Purpose**: Automated benchmarking with standard QA metrics.

**Components**:
- `metrics.py`: Evaluation metric implementations
- `benchmark.py`: Benchmarking framework
- `datasets/`: Dataset loaders

**Metrics Implemented**:
| Metric | Description |
|--------|-------------|
| Exact Match (EM) | Binary: 1 if prediction matches ground truth |
| F1 Score | Token-level overlap between prediction and truth |
| Recall@K | Proportion of relevant chunks in top-K retrieved |
| Precision@K | Proportion of top-K that are relevant |
| nDCG@10 | Normalized Discounted Cumulative Gain |
| MRR | Mean Reciprocal Rank |

**Usage**:
```bash
# Run evaluation on sample dataset
python evaluate_phase3.py --dataset sample

# Run ablation study
python evaluate_phase3.py --ablation

# Evaluate on custom dataset
python evaluate_phase3.py --dataset my_data.json --output results.json
```

---

## API Changes

### QueryResponse Model (Updated)

```python
class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    query_time_ms: int
    retrieved_chunks: int
    
    # Phase 3 additions
    confidence_score: Optional[float]  # 0.0 to 1.0
    confidence_level: Optional[str]    # "high", "medium", "low"
    answer_type: Optional[str]         # "generative" or "extractive"
    extractive_span: Optional[dict]    # Span info for highlighting
```

**Example Response**:
```json
{
  "answer": "The revenue grew by 25% in Q4 2024.",
  "citations": [...],
  "query_time_ms": 2341,
  "retrieved_chunks": 5,
  "confidence_score": 0.78,
  "confidence_level": "high",
  "answer_type": "generative",
  "extractive_span": null
}
```

**Extractive Response Example**:
```json
{
  "answer": "25%",
  "citations": [...],
  "query_time_ms": 1892,
  "retrieved_chunks": 5,
  "confidence_score": 0.92,
  "confidence_level": "high",
  "answer_type": "extractive",
  "extractive_span": {
    "start_char": 45,
    "end_char": 48,
    "chunk_index": 0
  }
}
```

---

## Configuration

### Environment Variables

```bash
# Phase 3: Confidence Scoring & Extractive Fallback
CONFIDENCE_THRESHOLD=0.4        # Below this, try extractive fallback
ENABLE_EXTRACTIVE_FALLBACK=true # Enable DistilBERT fallback
EXTRACTIVE_MODEL=distilbert-base-uncased-distilled-squad
MAX_REGENERATION_ATTEMPTS=1     # Regeneration attempts before fallback
```

### Config Class (`utils/config.py`)

```python
# Phase 3: Confidence scoring and extractive fallback
CONFIDENCE_THRESHOLD: float = 0.4
ENABLE_EXTRACTIVE_FALLBACK: bool = True
EXTRACTIVE_MODEL: str = "distilbert-base-uncased-distilled-squad"
MAX_REGENERATION_ATTEMPTS: int = 1
```

---

## Frontend Integration

### Confidence Display

The frontend now displays:
- **Confidence Score**: Percentage (e.g., 78%)
- **Confidence Level**: Color-coded indicator
  - 🟢 Green for high confidence (≥70%)
  - 🟡 Yellow for medium confidence (40-70%)
  - 🔴 Red for low confidence (<40%)
- **Answer Type Badge**: "AI Synthesis" or "Extracted Answer"

### Visual Components

```tsx
// Confidence indicator with tooltip
<Tooltip content="High Confidence - Answer is well-supported">
  <div className="bg-emerald-500/10 text-emerald-400">
    <CheckCircle className="w-3 h-3" />
    <span>78%</span>
  </div>
</Tooltip>

// Extractive answer badge
<span className="bg-amber-500/20 text-amber-400">
  Direct Quote
</span>
```

---

## Setup

### Dependencies

```bash
# Install Phase 3 dependencies
pip install rouge-score transformers datasets

# Or from requirements.txt
pip install -r requirements.txt
```

### Verify Installation

```bash
cd backend
python setup_phase3.py
```

### Download Models (First Run)

The DistilBERT model (~260MB) is downloaded automatically on first use.

---

## Usage

### Basic Query with Confidence

```python
# The query endpoint now returns confidence information
response = requests.post(
    "http://localhost:8000/api/query",
    json={"query": "What is the revenue growth?"}
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Confidence: {data['confidence_score']:.0%} ({data['confidence_level']})")
print(f"Type: {data['answer_type']}")
```

### Running Evaluation

```bash
# Basic evaluation
python evaluate_phase3.py --dataset sample

# Custom dataset
python evaluate_phase3.py --dataset my_questions.json --output results.json

# Ablation study
python evaluate_phase3.py --ablation --output evaluation_results/
```

---

## Performance

### Latency Impact

| Component | Additional Latency |
|-----------|-------------------|
| ROUGE-L scoring | 10-30ms |
| Extractive fallback (when triggered) | 100-200ms |
| Evaluation metrics | Offline only |

### Model Sizes

| Model | Size | Notes |
|-------|------|-------|
| DistilBERT | ~260MB | Downloaded on first use |
| Cross-encoder (Phase 2) | ~80MB | Already loaded |

---

## Troubleshooting

### Common Issues

**1. DistilBERT download fails**
```bash
# Manually download model
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")
model = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")
```

**2. Low confidence on good answers**
- Check that GPT is citing chunks properly with `[chunk_X]` format
- Verify citations contain relevant text
- Adjust `CONFIDENCE_THRESHOLD` if needed

**3. Extractive fallback always triggers**
- Increase `CONFIDENCE_THRESHOLD` (default: 0.4)
- Check that documents are properly indexed
- Ensure chunks contain answer information

**4. Evaluation script connection errors**
- Ensure backend is running on correct port
- Check `--api-url` parameter matches backend

---

## Technical Details

### ROUGE-L Algorithm

ROUGE-L uses Longest Common Subsequence (LCS) to measure similarity:

```python
def compute_rouge_l(candidate, reference):
    lcs_length = compute_lcs(candidate_tokens, reference_tokens)
    precision = lcs_length / len(candidate_tokens)
    recall = lcs_length / len(reference_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return f1
```

### Extractive QA

DistilBERT predicts start and end token positions:

```python
# Model outputs
start_logits, end_logits = model(input_ids, attention_mask)

# Get best span
start_idx = torch.argmax(start_logits)
end_idx = torch.argmax(end_logits)

# Decode answer
answer = tokenizer.decode(input_ids[start_idx:end_idx+1])
```

---

## Files Created/Modified

### New Files
- `backend/services/confidence_service.py` - ROUGE-L confidence scoring
- `backend/services/extractive_qa_service.py` - DistilBERT span extraction
- `backend/evaluation/__init__.py` - Evaluation module
- `backend/evaluation/metrics.py` - QA evaluation metrics
- `backend/evaluation/benchmark.py` - Benchmarking framework
- `backend/evaluation/datasets/sample_dataset.py` - Sample test data
- `backend/evaluate_phase3.py` - Evaluation script
- `backend/setup_phase3.py` - Setup verification
- `docs/PHASE3.md` - This documentation

### Modified Files
- `backend/requirements.txt` - Added Phase 3 dependencies
- `backend/utils/config.py` - Added Phase 3 configuration
- `backend/models/query.py` - Extended QueryResponse model
- `backend/services/__init__.py` - Export new services
- `backend/services/answer_generator.py` - Integrated confidence + fallback
- `backend/routes/query.py` - Updated to use Phase 3 features
- `frontend/src/app/page.tsx` - Confidence state management
- `frontend/src/components/AnswerDisplay.tsx` - Confidence UI
- `env.example` - Phase 3 environment variables

---

## Next Steps (Phase 4 Ideas)

- **Coreference Resolution**: Advanced pronoun handling for multi-hop
- **Production Deployment**: Vercel + Railway with caching
- **Model Fine-tuning**: Domain-specific extractive QA
- **Active Learning**: User feedback loop for improvements

---

**Phase 3 Complete!** 🎉

The system now provides:
- ✅ Confidence scoring for answer validation
- ✅ Extractive fallback for low-confidence cases
- ✅ Comprehensive evaluation metrics
- ✅ Visual confidence indicators in UI


