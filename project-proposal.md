# Intelligent Document Q&A System — Final Proposal

**Course:** COMP 4750 – Natural Language Processing  
**Submission:** Streamlit demo + technical report + evaluation notebook

---

## 1. Project Overview

We will deliver an intelligent assistant that answers natural-language questions about heterogeneous enterprise documents (PDFs, scans, Word files, rich-text manuals). The assistant keeps GPT for final response generation but wraps it in a purposely engineered NLP pipeline that:

- Understands the document layout (paragraphs, tables, captions).  
- Retrieves evidence using both dense embeddings and lightweight lexical cues.  
- Reranks results with a cross-encoder for semantic precision.  
- Plans multi-hop queries deterministically before calling an LLM.  
- Returns citation-backed answers with an explicit confidence signal.

All NLP components rely on established, publicly available models; no custom training or fine-tuning is required.

---

## 2. Motivation & Problem Statement

Organizations store decisions, compliance obligations, and procedures inside long PDFs or scanned contracts. Existing “RAG” demos often ignore layout, conflate unrelated clauses, and rarely warn users when citations are weak. Our goal is to remove that ambiguity by pairing GPT with targeted NLP components so users can trust both the answer and the evidence path.

---

## 3. Prior Work & Rationale

- **Dense Passage Retrieval (DPR)** and the RAG architecture (Lewis et al., 2020) popularized dual-encoder retrieval plus LLM generation.  
- **PIER-QA (Hoang & Nguyen, 2025)** and **eSapiens (Shi et al., 2025)** showed multimodal PDF understanding for enterprise search but require heavy infrastructure.  
- Academic datasets such as **Natural Questions** and **DocVQA** provide benchmarks for QA over semi-structured text.  

We adopt RAG as the foundation yet add lightweight, purpose-driven NLP steps to address layout fidelity, retrieval precision, and answer trustworthiness for a course-scale project.

---

## 4. System Architecture (High-Level)

1. **Ingestion + Layout Parsing:** Extract text, bounding boxes, and block types from PDFs/images using `pdfminer.six`, `pytesseract`, and `layoutparser` with `PubLayNet` weights.  
2. **Chunking + Metadata:** Split content into layout-aware chunks tagged with `{section, block_type, bbox, page}`.  
3. **Hybrid Retrieval:**  
   - Dense embeddings via `text-embedding-3-large` (primary) or `sentence-transformers/all-MiniLM-L6-v2` (offline fallback) stored in `Qdrant`.  
   - Lexical support through BM25 (`Elasticsearch`) plus YAKE keywords per chunk.  
   - Weighted score fusion for candidate selection.  
4. **Hybrid Reranker:** Re-score top 20 candidates using `cross-encoder/ms-marco-MiniLM-L-6-v2`; retain top 5.  
5. **Query Planner:** Analyze user queries with `spaCy` dependency parsing and clause segmentation, detect multi-hop references, and orchestrate sequential retrieval calls.  
6. **Answering + Confidence Gate:** Prompt GPT-5-mini using reranked context. Compute citation overlap; low overlap triggers regeneration or an extractive fallback (`distilbert-base-uncased-distilled-squad`).  
7. **UI & Reporting:** Streamlit front-end showing answer, citations, highlighted evidence, confidence meter, and retrieval diagnostics.

---

## 5. Key NLP Enhancements (Course Deliverables)

| Enhancement | Purpose | Implementation Detail |
| --- | --- | --- |
| Layout-aware parsing | Preserve document structure for precise retrieval | `layoutparser` + `Detectron2` checkpoints; metadata injected into chunk schema |
| Hybrid lexical signals | Improve short-query precision without training | BM25 score + YAKE keyword overlap combined with dense cosine similarity |
| Hybrid reranker | Semantic precision beyond vector search | `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks top candidates |
| Query planner | Deterministic multi-hop reasoning | `spaCy` dependency trees + clause detection to split/sequence sub-queries |
| Confidence + citation gate | Trustworthy answers | ROUGE-L overlap between answer sentences and cited spans; low scores trigger regeneration/extractive fallback |

These components together constitute the “non-generic” NLP work expected in COMP 4750 without requiring custom training.

---

## 6. Detailed Workflow

1. **Document Intake**  
   - User uploads PDFs, Word docs, or images.  
   - Convert everything to PDF if needed, then extract text layers.  
   - OCR via `pytesseract` for images; fallback to `docTR` when handwriting is detected.  

2. **Layout Parsing & Chunking**  
   - Run `layoutparser` with `PubLayNet` or `Donut` checkpoints to detect paragraphs, tables, figures, captions, headers.  
   - Combine bounding boxes with text spans; chunk per logical block (paragraph or table row).  
   - Store metadata fields such as `doc_id`, `page`, `bbox`, `block_type`, `section_heading`.

3. **Semantic + Lexical Indexing**  
   - Dense embeddings computed once and saved in `Qdrant`.  
   - Text copied into `Elasticsearch` for BM25 retrieval.  
   - YAKE keywords (top 10) stored for fast overlap scoring.  
   - Score fusion: `score = 0.5 * cosine + 0.3 * BM25_norm + 0.2 * keyword_overlap`.

4. **Query Understanding**  
   - `spaCy` pipeline extracts clauses, question words, temporal modifiers.  
   - Pronoun resolution via lightweight neural coreference (`en_coreference_web_trf`).  
   - Multi-hop detection: if multiple clauses or coreferent references exist, create ordered sub-queries (e.g., “When was Contract X signed?” then “Who signed it?”).

5. **Retrieval & Reranking**  
   - Run dense + lexical retrieval per (sub-)query; merge candidate sets (k=40).  
   - Apply cross-encoder reranker; keep top 5 chunks per hop.  
   - For multi-hop, maintain evidence graph describing which chunk answers each sub-question.

6. **Answer Generation**  
   - Compose structured prompt: sub-query summary, reranked chunks with layout tags, instructions to cite chunk IDs.  
   - GPT produces an answer with inline `[chunk_id]` citations plus a short “How confident are we?” rationale.

7. **Confidence & Fallback**  
   - Compute ROUGE-L/token overlap between answer sentences and cited chunks.  
   - Display normalized score (0–1) as confidence bar; threshold 0.6.  
   - If below threshold, auto-regenerate answer with stricter instructions; if still low, fall back to extractive highlight sourced from best chunk.

8. **UI Presentation**  
   - Streamlit shows answer, confidence gauge, citations expandable to highlight original PDF snippets with bounding boxes.  
   - Debug sidebar exposes retrieval weights, reranker scores, and planner steps for instructors.

---

## 7. Implementation Plan & Tech Stack

- **Languages:** Python 3.11 (backend + processing), TypeScript (optional for custom components in Streamlit).  
- **Frameworks:** FastAPI (API), Streamlit (UI), Celery (optional for async ingestion).  
- **Libraries / Models:** `pdfminer.six`, `pytesseract`, `layoutparser`, `sentence-transformers`, `spaCy`, `yaake`, `Qdrant-client`, `Elasticsearch`, OpenAI GPT-5-mini.
- **Storage:** `Qdrant` for embeddings, `Elasticsearch` for lexical index, `PostgreSQL` for metadata + logs.  
- **Deployment:** Docker Compose for local orchestration; optional Railway/Render for demo hosting.

No custom training: every model listed above ships pre-trained and will be used as-is.

---

## 8. Evaluation Strategy

1. **Datasets**  
   - 10 internal documents supplied by the course (contracts, manuals).  
   - Public subsets: `DocVQA Task 1`, `Natural Questions` long-answer subset, `Pile of Law` snippets.  

2. **Metrics**  
   - Retrieval Recall@5 / nDCG@10 (baseline vs. hybrid vs. reranked).  
   - Answer Exact Match & token-level F1 (for extractive fallback).  
   - Citation coverage (%) = proportion of answer tokens supported by retrieved text.  
   - Confidence calibration: correlation between overlap score and human trust ratings.  

3. **Procedures**  
   - Ablation study toggling each enhancement.  
   - 5-person user study: participants judge accuracy/trust for 15 questions with and without the confidence gate.  
   - Report latency measurements for each pipeline stage.

---

## 9. Focus and Milestones

| # | Focus | Milestones |
| --- | --- | --- |
| 1 | Intake & Layout | End-to-end ingestion, layout metadata persisted |
| 2 | Hybrid Retrieval | Dense + BM25 fusion working; YAKE keywords cached |
| 3 | Reranker + UI | Cross-encoder reranker integrated; Streamlit evidence viewer |
| 4 | Query Planner | Multi-hop parsing + orchestration validated on sample tasks |
| 5 | Confidence Gate | Overlap scoring, regeneration/fallback logic, UI gauge |
| 6 | Evaluation & Polish | Metrics computed, ablations logged, final report drafted |

Weekly demos ensure instructor visibility into incremental progress.

---

## 10. Risks & Mitigations

- **OCR Noise:** Switch to `docTR` for handwriting, run rule-based cleanup (ligatures, hyphenation) before chunking.  
- **Latency / Cost:** Cache embeddings per document, batch reranker requests, allow local embedding fallback.  
- **API Failure:** Provide offline mode using `all-MiniLM` embeddings + `Llama 3.1 8B` local generation (for limited demos).  
- **Complex Queries:** Planner logs unresolved references; UI prompts user for clarification if dependency parsing confidence < 0.5.

---

## 11. Deliverables

1. **Codebase** (GitHub) with FastAPI service, Streamlit UI, Docker Compose, and environment scripts.  
2. **Demo Video** walking through ingestion, query planner visualization, and confidence gate behavior.  
3. **Evaluation Notebook** (Jupyter) replicating metrics, ablations, and user study summaries.  
4. **Final Report** detailing architecture, experiments, lessons learned, and limitations.

This proposal satisfies the COMP 4750 requirement for an NLP-heavy project by embedding multiple established NLP models in a cohesive, reproducible system while keeping scope realistic for a final-year effort.

