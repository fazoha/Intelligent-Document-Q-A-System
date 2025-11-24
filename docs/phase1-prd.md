# Phase 1 PRD: Core Pipeline & Foundation
**Intelligent Document Q&A System**  
**COMP 4750 — Natural Language Processing**

---

## 1. Executive Summary

Phase 1 establishes the foundational infrastructure for the Intelligent Document Q&A System: a production-grade ingestion pipeline, layout-aware parsing, baseline dense retrieval, and an interactive Next.js + FastAPI UI. By the end of this phase, users can upload documents (PDFs, images, Word files), ask natural-language questions, and receive GPT-generated answers backed by citations from the document corpus.

**Key Deliverable:** A working end-to-end prototype demonstrating document intake → chunking with layout metadata → semantic search → answer generation with inline citations.

**What Phase 1 Does:**
- Accept PDF, DOCX, PNG/JPG uploads via a clean web UI
- Parse documents using Unstructured.io to extract text and layout metadata (paragraphs, tables, headers)
- Chunk content intelligently while preserving bounding boxes, page numbers, and block types
- Generate dense embeddings and store them in Upstash Vector DB
- Perform baseline cosine-similarity retrieval against user queries
- Call OpenAI gpt-5-mini to generate context-aware answers with chunk citations
- Display results in a polished Next.js + Tailwind interface with expandable citation previews

**What Phase 1 Does NOT Do (reserved for Phases 2 & 3):**
- Hybrid lexical retrieval (BM25, YAKE keywords) — Phase 2
- Cross-encoder reranking — Phase 2
- Query planner (multi-hop reasoning, pronoun resolution) — Phase 2
- Confidence scoring + citation gate — Phase 3
- Extractive fallback answers — Phase 3
- Evaluation harness or ablation studies — Phase 3

---

## 2. Success Criteria

Phase 1 is considered **complete** when:

1. ✅ Users can upload PDFs, images, or Word documents via the web UI without errors
2. ✅ Documents are parsed and chunked with layout metadata (section, bbox, page, block_type) persisted
3. ✅ Chunks are embedded using OpenAI `text-embedding-3-large` and stored in Upstash Vector
4. ✅ Users can submit a natural-language query and receive semantically relevant chunks (top-5)
5. ✅ gpt-5-mini generates an answer referencing chunk IDs, displayed in the UI with expandable citations
6. ✅ The system logs all pipeline stages (ingestion, embedding, retrieval, generation) for debugging
7. ✅ End-to-end latency for a typical query is < 5 seconds (excluding file upload)
8. ✅ The codebase follows clean architecture patterns, is well-documented, and runs reliably via `npm run dev`

---

## 3. Scope & Constraints

### 3.1 In Scope (Phase 1)

- **Document Ingestion:**
  - Support for PDF, PNG/JPG (OCR via Unstructured.io), DOCX files
  - Async processing using FastAPI background tasks
  - Basic error handling for corrupt/unsupported files

- **Layout-Aware Parsing:**
  - Leverage Unstructured.io API to extract text + layout metadata
  - Store chunk-level metadata: `doc_id`, `chunk_id`, `page`, `bbox`, `block_type` (paragraph, table, heading, etc.), `section_heading`
  - Schema design to accommodate future retrieval enhancements

- **Baseline Dense Retrieval:**
  - Embed chunks using OpenAI `text-embedding-3-large` (1536 dimensions)
  - Store embeddings in Upstash Vector DB (serverless, no local hosting)
  - Cosine similarity search returning top-5 chunks per query

- **Answer Generation:**
  - Compose gpt-5-mini prompt with user query + top-5 retrieved chunks
  - Instruct GPT to cite chunk IDs inline (e.g., `[chunk_42]`)
  - Return structured response: `{answer: string, citations: [{chunk_id, text, page, bbox}]}`

- **UI/UX:**
  - Next.js 14 (App Router) + Tailwind CSS
  - Single-page application with upload zone, question input, and answer display
  - Citation cards expandable to show source text, page number, and bounding box coordinates
  - Loading states, error messages, and empty states

- **Infrastructure:**
  - FastAPI backend (Python 3.11+) with async endpoints
  - Next.js frontend (TypeScript, React Server Components where applicable)
  - Upstash Vector DB (free tier for development)
  - OpenAI API (gpt-5-mini + embeddings)
  - Environment secrets managed via `.env` files (not committed)

### 3.2 Out of Scope (Phase 1)

- BM25 or keyword-based lexical retrieval (Phase 2)
- Cross-encoder reranking models (Phase 2)
- Query parsing, multi-hop planning, pronoun resolution (Phase 2)
- Confidence scoring, citation overlap metrics, extractive fallback (Phase 3)
- User authentication, multi-user sessions, document ownership
- Cloud deployment (Vercel, Railway) — local development only
- Advanced OCR (handwriting detection, table extraction refinement)
- Real-time collaboration or document versioning

### 3.3 Constraints & Assumptions

- **API Dependencies:** OpenAI API and Unstructured.io API must be available; rate limits respected
- **Upstash Free Tier:** 10,000 queries/day, 10,000 updates/day (sufficient for development)
- **No Local Vector DB:** Qdrant/Weaviate/Chroma are NOT used; Upstash Vector is the sole vector store
- **No Fine-Tuning:** All models (gpt-5-mini, embeddings) used as-is via API
- **Single-Document Corpus:** Phase 1 assumes all uploaded documents belong to a single corpus; no per-user isolation
- **Synchronous Embedding:** Documents are embedded synchronously on upload (async job queue deferred to later optimization)
- **Browser Support:** Modern Chrome/Firefox/Safari; no IE11 compatibility required

---

## 4. Functional Requirements

### 4.1 User Stories

**US-1: Upload Document**  
_As a user, I want to upload a PDF, image, or Word document so the system can index its contents for question-answering._

- **Acceptance Criteria:**
  - Drag-and-drop or file picker UI accepts `.pdf`, `.png`, `.jpg`, `.jpeg`, `.docx` files
  - Upload triggers FastAPI `/api/documents/upload` endpoint
  - Backend validates file type and size (max 10MB)
  - Document is parsed via Unstructured.io, chunked, embedded, and stored in Upstash
  - UI shows progress spinner and success/error toast notification
  - Uploaded document appears in a "Documents" sidebar list with filename, page count, upload timestamp

**US-2: Ask Question**  
_As a user, I want to type a natural-language question so I can get an answer grounded in the uploaded documents._

- **Acceptance Criteria:**
  - Text input field with placeholder "Ask a question about your documents..."
  - Submit triggers FastAPI `/api/query` endpoint with `{query: string}`
- Backend embeds query, retrieves top-5 chunks, calls gpt-5-mini, returns `{answer, citations}`
  - UI displays answer in a readable card with citations as expandable tags
  - Latency from submit to answer display < 5 seconds

**US-3: View Citations**  
_As a user, I want to see which document chunks support the answer so I can verify its accuracy._

- **Acceptance Criteria:**
  - Each citation tag shows `[chunk_id]` inline within the answer text
  - Clicking a citation expands a card showing: source text, page number, bounding box coordinates, document name
  - Multiple citations can be expanded simultaneously
  - Citation cards are visually linked (e.g., color-coded) to the answer text

**US-4: Clear Session**  
_As a user, I want to clear all uploaded documents and start fresh._

- **Acceptance Criteria:**
  - "Clear All" button in the UI
  - Confirmation modal ("Are you sure? This will delete all documents and embeddings.")
  - Backend `/api/documents/clear` endpoint removes all vectors from Upstash and metadata from temporary storage
  - UI resets to empty state

### 4.2 System Workflows

**Workflow 1: Document Upload & Indexing**

```
[User] → Upload file (PDF/image/DOCX)
  ↓
[Next.js] → POST /api/documents/upload (FormData)
  ↓
[FastAPI] → Validate file type/size
  ↓
[FastAPI] → Call Unstructured.io API (parse document → elements with metadata)
  ↓
[FastAPI] → Chunk elements (group by section, max 512 tokens per chunk)
  ↓
[FastAPI] → For each chunk:
              - Generate embedding (OpenAI text-embedding-3-large)
              - Upsert to Upstash Vector (id, vector, metadata: {doc_id, page, bbox, block_type, text})
  ↓
[FastAPI] → Return {doc_id, chunk_count, status: "indexed"}
  ↓
[Next.js] → Display success toast + add document to sidebar
```

**Workflow 2: Query & Answer Generation**

```
[User] → Type question, click "Ask"
  ↓
[Next.js] → POST /api/query (JSON: {query: string})
  ↓
[FastAPI] → Embed query (OpenAI text-embedding-3-large)
  ↓
[FastAPI] → Query Upstash Vector (cosine similarity, top_k=5)
  ↓
[FastAPI] → Retrieve chunk metadata (text, page, bbox, doc_id)
  ↓
[FastAPI] → Compose gpt-5-mini prompt:
            """
            Context:
            [chunk_1] (page 3, paragraph): {text}
            [chunk_2] (page 7, table): {text}
            ...

            Question: {query}

            Answer the question using only the provided context. Cite chunks inline using [chunk_id].
            """
  ↓
[FastAPI] → Call OpenAI gpt-5-mini → parse response
  ↓
[FastAPI] → Return {answer: string, citations: [{chunk_id, text, page, bbox, doc_name}]}
  ↓
[Next.js] → Render answer with clickable citation tags
```

### 4.3 API Contracts

**Endpoint: `POST /api/documents/upload`**

- **Request:**
  ```
  Content-Type: multipart/form-data
  Body: file (binary)
  ```

- **Response (Success 200):**
  ```json
  {
    "doc_id": "uuid-v4-string",
    "filename": "contract.pdf",
    "page_count": 12,
    "chunk_count": 47,
    "status": "indexed",
    "uploaded_at": "2026-01-15T10:30:00Z"
  }
  ```

- **Response (Error 400):**
  ```json
  {
    "error": "Unsupported file type. Only PDF, PNG, JPG, DOCX allowed."
  }
  ```

**Endpoint: `POST /api/query`**

- **Request:**
  ```json
  {
    "query": "What is the termination clause in the employment contract?"
  }
  ```

- **Response (Success 200):**
  ```json
  {
    "answer": "The termination clause [chunk_23] states that either party may terminate with 30 days written notice [chunk_24].",
    "citations": [
      {
        "chunk_id": "chunk_23",
        "text": "Either party may terminate this agreement by providing...",
        "page": 5,
        "bbox": [100, 200, 500, 250],
        "doc_name": "employment_contract.pdf",
        "block_type": "paragraph"
      },
      {
        "chunk_id": "chunk_24",
        "text": "...30 days written notice to the other party.",
        "page": 5,
        "bbox": [100, 260, 500, 290],
        "doc_name": "employment_contract.pdf",
        "block_type": "paragraph"
      }
    ],
    "query_time_ms": 3421
  }
  ```

- **Response (Error 404):**
  ```json
  {
    "error": "No documents indexed. Please upload a document first."
  }
  ```

**Endpoint: `DELETE /api/documents/clear`**

- **Request:** None

- **Response (Success 200):**
  ```json
  {
    "message": "All documents and embeddings cleared.",
    "deleted_count": 47
  }
  ```

**Endpoint: `GET /api/documents`**

- **Request:** None

- **Response (Success 200):**
  ```json
  {
    "documents": [
      {
        "doc_id": "uuid-1",
        "filename": "contract.pdf",
        "page_count": 12,
        "chunk_count": 47,
        "uploaded_at": "2026-01-15T10:30:00Z"
      },
      {
        "doc_id": "uuid-2",
        "filename": "manual.docx",
        "page_count": 8,
        "chunk_count": 32,
        "uploaded_at": "2026-01-15T11:00:00Z"
      }
    ]
  }
  ```

---

## 5. Technical Architecture

### 5.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Next.js 14 (App Router) + Tailwind CSS           │   │
│  │  - Upload UI (drag-drop, file picker)                    │   │
│  │  - Question Input (text field + submit)                  │   │
│  │  - Answer Display (citations expandable)                 │   │
│  │  - Document Sidebar (list of uploaded docs)              │   │
│  └─────────────────┬────────────────────────────────────────┘   │
└────────────────────┼────────────────────────────────────────────┘
                     │ HTTP/JSON
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Python 3.11+)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Routes:                                             │   │
│  │  - POST /api/documents/upload                            │   │
│  │  - POST /api/query                                       │   │
│  │  - GET /api/documents                                    │   │
│  │  - DELETE /api/documents/clear                           │   │
│  └─────────────────┬────────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────┴────────────────────────────────────────┐   │
│  │  Core Services:                                          │   │
│  │  - DocumentParser (Unstructured.io integration)          │   │
│  │  - ChunkBuilder (layout-aware chunking)                  │   │
│  │  - EmbeddingService (OpenAI text-embedding-3-large)      │   │
│  │  - VectorStore (Upstash Vector client)                   │   │
│  │  - AnswerGenerator (gpt-5-mini prompt orchestration)        │   │
│  └─────────────────┬────────────────────────────────────────┘   │
└────────────────────┼────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌────────────┐ ┌──────────────────┐
│ Unstructured │ │  OpenAI    │ │  Upstash Vector  │
│     .io      │ │    API     │ │       DB         │
│              │ │            │ │                  │
│ - Parse PDF  │ │ - Embed    │ │ - Store vectors  │
│ - Extract    │ │ - gpt-5-mini  │ │ - Cosine search  │
│   layout     │ │   answer   │ │ - Metadata       │
└──────────────┘ └────────────┘ └──────────────────┘
```

### 5.2 Data Models

**Document Model (In-Memory / Temp Storage)**
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Document(BaseModel):
    doc_id: str  # UUID v4
    filename: str
    file_type: str  # "pdf", "image", "docx"
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str  # "processing", "indexed", "failed"
```

**Chunk Model (Upstash Vector Metadata)**
```python
class ChunkMetadata(BaseModel):
    doc_id: str
    chunk_id: str  # e.g., "chunk_0", "chunk_1", ...
    text: str  # raw chunk text (max 512 tokens)
    page: int
    bbox: List[float]  # [x1, y1, x2, y2] coordinates
    block_type: str  # "paragraph", "table", "heading", "caption", "footer"
    section_heading: Optional[str]  # nearest heading above this chunk
    doc_name: str  # original filename for citation display
```

**Query Request Model**
```python
class QueryRequest(BaseModel):
    query: str
```

**Query Response Model**
```python
class Citation(BaseModel):
    chunk_id: str
    text: str
    page: int
    bbox: List[float]
    doc_name: str
    block_type: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    query_time_ms: int
```

### 5.3 Technology Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| **Frontend** | Next.js | 14.2.23 | Modern React framework with App Router, server components, excellent DX |
| | TypeScript | 5.6.2 | Type safety, autocomplete, better maintainability |
| | Tailwind CSS | 3.4.12 | Rapid UI prototyping, utility-first CSS |
| | clsx / tailwind-merge | Latest | Conditional className logic |
| **Backend** | FastAPI | 0.115.0 | High-performance async Python web framework, auto OpenAPI docs |
| | Uvicorn | 0.30.6 | ASGI server for FastAPI |
| | Python | 3.11+ | Modern Python with improved async performance |
| | Pydantic | Latest | Data validation, schema definition |
| **Document Processing** | Unstructured.io API | Latest | Cloud-based document parsing, layout detection, no local setup |
| **Embeddings** | OpenAI API | Latest | `text-embedding-3-large` (1536 dims), industry-leading quality |
| **LLM** | OpenAI API | Latest | gpt-5-mini (primary) or GPT-5-mini fallback for answer generation |
| **Vector DB** | Upstash Vector | Latest | Serverless vector DB, no local hosting, REST API, free tier |
| **Environment** | python-dotenv | Latest | Manage `.env` secrets |
| | concurrently | 9.0.1 | Run Next.js + FastAPI dev servers simultaneously |

### 5.4 Integration Details

#### 5.4.1 Upstash Vector Setup

1. **Account Setup:**
   - Create free account at [console.upstash.com](https://console.upstash.com)
   - Navigate to Vector tab → Create Index
   - Configuration:
     - **Name:** `nlp-doc-qa-dev`
     - **Type:** Dense
     - **Dimensions:** 1536 (matches OpenAI `text-embedding-3-large`)
     - **Distance Metric:** Cosine
     - **Region:** Closest to developer location (e.g., `us-east-1`)
   - Copy `UPSTASH_VECTOR_REST_URL` and `UPSTASH_VECTOR_REST_TOKEN` to `.env`

2. **Python Client Integration:**
   ```python
   from upstash_vector import Index

   index = Index(
       url=os.getenv("UPSTASH_VECTOR_REST_URL"),
       token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
   )

   # Upsert vectors
   index.upsert(
       vectors=[
           (chunk_id, embedding_vector, chunk_metadata_dict)
       ]
   )

   # Query vectors
   results = index.query(
       vector=query_embedding,
       top_k=5,
       include_metadata=True
   )
   ```

3. **Schema Conventions:**
   - Vector ID format: `{doc_id}::{chunk_index}` (e.g., `uuid-123::0`)
   - Metadata fields: `doc_id`, `chunk_id`, `text`, `page`, `bbox`, `block_type`, `section_heading`, `doc_name`

#### 5.4.2 OpenAI API Integration

**Environment Variables:**
```bash
OPENAI_API_KEY=sk-proj-...
```

**Embedding Generation:**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_text(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding
```

**Answer Generation:**
```python
def generate_answer(query: str, chunks: List[ChunkMetadata]) -> str:
    context = "\n\n".join([
        f"[{chunk.chunk_id}] (page {chunk.page}, {chunk.block_type}):\n{chunk.text}"
        for chunk in chunks
    ])
    
    prompt = f"""Context from documents:
{context}

Question: {query}

Instructions:
- Answer the question using ONLY the provided context.
- Cite sources inline using [chunk_id] format.
- If the context doesn't contain enough information, say "I don't have enough information to answer this question."
- Be concise and precise.

Answer:"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": "You are a helpful document assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        reasoning={"effort": "low"},
        text={"verbosity": "low"}
    )
    
    return response.output_text
```

#### 5.4.3 Unstructured.io API Integration

**Environment Variables:**
```bash
UNSTRUCTURED_API_KEY=your-api-key
UNSTRUCTURED_API_URL=https://api.unstructured.io/general/v0/general
```

**Document Parsing:**
```python
import requests

def parse_document(file_path: str) -> List[dict]:
    """
    Parse document using Unstructured.io API.
    Returns list of elements with text, type, metadata (bbox, page).
    """
    with open(file_path, "rb") as f:
        files = {"files": f}
        headers = {"unstructured-api-key": os.getenv("UNSTRUCTURED_API_KEY")}
        
        response = requests.post(
            os.getenv("UNSTRUCTURED_API_URL"),
            files=files,
            headers=headers,
            data={
                "strategy": "hi_res",  # high-resolution parsing
                "coordinates": "true",  # include bounding boxes
                "pdf_infer_table_structure": "true"
            }
        )
        
    return response.json()  # List of elements with type, text, metadata
```

**Element Types:** `Title`, `NarrativeText`, `Table`, `ListItem`, `Header`, `Footer`, `FigureCaption`, etc.

### 5.5 File & Directory Structure

```
may-project/
├── docs/
│   ├── phase1-prd.md (this file)
│   └── project-proposal.md
├── nextjs-fastapi/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx (main UI)
│   │   └── globals.css
│   ├── components/
│   │   ├── UploadZone.tsx
│   │   ├── QuestionInput.tsx
│   │   ├── AnswerDisplay.tsx
│   │   ├── CitationCard.tsx
│   │   └── DocumentSidebar.tsx
│   ├── api/
│   │   ├── index.py (FastAPI app)
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   └── query.py
│   │   ├── services/
│   │   │   ├── document_parser.py
│   │   │   ├── chunk_builder.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_store.py
│   │   │   └── answer_generator.py
│   │   ├── models/
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   └── query.py
│   │   └── utils/
│   │       ├── logger.py
│   │       └── config.py
│   ├── public/
│   ├── package.json
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env (gitignored)
│   └── README.md
└── project-proposal-draft.md
```

---

## 6. UI/UX Specifications

### 6.1 Design Principles

- **Simplicity First:** Clean, uncluttered interface focused on core workflows (upload, query, view)
- **Immediate Feedback:** Loading states, progress indicators, success/error toasts
- **Citation Transparency:** Every claim in the answer should be traceable to a source chunk
- **Responsive Layout:** Desktop-first (1440px), tablet-friendly (768px+), mobile-readable (375px+)
- **Accessibility:** WCAG 2.1 AA compliance (semantic HTML, ARIA labels, keyboard navigation)

### 6.2 Page Layout (Single-Page Application)

```
┌────────────────────────────────────────────────────────────────┐
│  Header: "Intelligent Document Q&A"  [Clear All]               │
├──────────────┬─────────────────────────────────────────────────┤
│              │                                                  │
│  Documents   │  Main Area                                       │
│  Sidebar     │  ┌────────────────────────────────────────────┐ │
│  ┌────────┐  │  │  Upload Zone (if no docs)                  │ │
│  │ Doc 1  │  │  │  Drag & drop or click to upload            │ │
│  │ 12 pgs │  │  │  Supported: PDF, PNG, JPG, DOCX            │ │
│  └────────┘  │  └────────────────────────────────────────────┘ │
│  ┌────────┐  │                                                  │
│  │ Doc 2  │  │  ┌────────────────────────────────────────────┐ │
│  │ 8 pgs  │  │  │  Question Input                            │ │
│  └────────┘  │  │  "Ask a question about your documents..."  │ │
│              │  │  [Ask] button                              │ │
│  [+ Upload]  │  └────────────────────────────────────────────┘ │
│              │                                                  │
│              │  ┌────────────────────────────────────────────┐ │
│              │  │  Answer Display                            │ │
│              │  │  The termination clause [chunk_23] states  │ │
│              │  │  that either party may...                  │ │
│              │  │                                            │ │
│              │  │  Citations:                                │ │
│              │  │  [chunk_23] ▼ (click to expand)            │ │
│              │  │    → "Either party may terminate..."       │ │
│              │  │    → Page 5, Paragraph                     │ │
│              │  │    → BBox: [100, 200, 500, 250]            │ │
│              │  └────────────────────────────────────────────┘ │
│              │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

### 6.3 Component Specifications

**UploadZone.tsx**
- Tailwind classes: `border-dashed border-2 border-gray-300 rounded-lg p-8 hover:border-emerald-500 transition`
- States: `idle`, `dragover`, `uploading`, `success`, `error`
- Displays file name, size, progress bar during upload
- Toast notification on success/error

**QuestionInput.tsx**
- Textarea (auto-resize, max 3 lines)
- Submit button disabled if input empty or query in progress
- Loading spinner inside button during query execution

**AnswerDisplay.tsx**
- Markdown-style rendering (bold, italics, lists)
- Citation tags rendered as clickable chips (e.g., `<span className="citation-tag">[chunk_23]</span>`)
- Empty state: "No answer yet. Ask a question to get started."

**CitationCard.tsx**
- Expandable accordion component
- Shows: chunk text (truncated to 200 chars), page number, block type, bounding box
- Copy-to-clipboard button for chunk text
- Subtle highlight animation when expanded

**DocumentSidebar.tsx**
- List of uploaded documents (max 10 visible, scroll if more)
- Each item shows: filename, page count, upload time (relative, e.g., "2 hours ago")
- Delete icon per document (confirmation modal)
- "+ Upload" button at bottom

### 6.4 Tailwind Theme Customization

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#10b981', // emerald-500
        secondary: '#6b7280', // gray-500
        background: '#f9fafb', // gray-50
        surface: '#ffffff',
        error: '#ef4444', // red-500
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
```

---

## 7. Implementation Milestones (Phase 1 Internal)

| Milestone | Tasks | Estimated Effort | Validation |
|-----------|-------|------------------|------------|
| **M1: Foundation** | - FastAPI skeleton with CORS, logging<br>- Next.js app scaffold with Tailwind<br>- Environment setup (`.env`, Upstash, OpenAI keys) | 4 hours | `GET /api/` returns `{"message": "Hello World"}` |
| **M2: Document Upload** | - `POST /api/documents/upload` endpoint<br>- Unstructured.io integration<br>- File validation, temp storage<br>- Upload UI component | 8 hours | Upload a PDF → see parsed elements logged |
| **M3: Chunking + Embedding** | - ChunkBuilder service (layout-aware chunking)<br>- EmbeddingService (OpenAI integration)<br>- VectorStore service (Upstash client) | 8 hours | Upload PDF → chunks stored in Upstash with metadata |
| **M4: Retrieval** | - `POST /api/query` endpoint<br>- Query embedding + vector search<br>- Return top-5 chunks with metadata | 4 hours | Query "termination clause" → returns relevant chunks |
| **M5: Answer Generation** | - AnswerGenerator service (gpt-5-mini prompting)<br>- Citation parsing from GPT response<br>- QueryResponse model | 6 hours | Query → returns answer with `[chunk_id]` citations |
| **M6: UI Integration** | - QuestionInput component<br>- AnswerDisplay component<br>- CitationCard component<br>- Wire frontend to FastAPI backend | 8 hours | End-to-end UI flow works (upload → query → answer) |
| **M7: Document Sidebar** | - `GET /api/documents` endpoint<br>- DocumentSidebar component<br>- `DELETE /api/documents/{doc_id}` endpoint<br>- Clear All functionality | 4 hours | Sidebar shows uploaded docs; delete works |
| **M8: Polish & Testing** | - Error handling (file too large, API failures)<br>- Loading states, toasts, empty states<br>- Responsive CSS tweaks<br>- Manual end-to-end testing | 6 hours | Stable, polished UX; no crashes on edge cases |

**Total Estimated Effort:** ~48 hours (~1 week full-time, ~2 weeks part-time)

---

## 8. Testing Strategy

### 8.1 Unit Tests (Deferred to Phase 2)

Phase 1 focuses on integration and manual testing. Unit tests for services (chunking, embedding, vector search) will be added in Phase 2.

### 8.2 Integration Tests

**Test Case: Upload & Index PDF**
- Upload `sample_contract.pdf` (3 pages)
- Verify: 200 response, `chunk_count > 0`, Upstash index contains vectors

**Test Case: Query Returns Relevant Chunks**
- Upload document with known content (e.g., "The termination clause is on page 5.")
- Query: "Where is the termination clause?"
- Verify: Response includes chunk from page 5

**Test Case: GPT Citations Match Retrieved Chunks**
- Query returns answer with `[chunk_23]`
- Verify: `chunk_23` exists in `citations` array with correct metadata

### 8.3 Manual End-to-End Testing

**Scenario 1: Happy Path**
1. Open `http://localhost:3000`
2. Upload `employment_contract.pdf`
3. Wait for success toast
4. Type: "What is the salary mentioned in the contract?"
5. Click "Ask"
6. Verify: Answer appears with citations
7. Click citation tag → verify card expands with source text

**Scenario 2: Error Handling**
1. Upload 50MB file → verify error toast "File too large"
2. Upload `.txt` file → verify error "Unsupported file type"
3. Query without uploading docs → verify message "No documents indexed"

**Scenario 3: Multiple Documents**
1. Upload `contract.pdf` and `manual.docx`
2. Query: "What is the warranty policy?"
3. Verify: Answer cites chunks from `manual.docx` (not `contract.pdf`)

### 8.4 Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Upload → Indexed (10-page PDF) | < 15 seconds | Time from upload submit to success toast |
| Query → Answer (simple question) | < 5 seconds | Time from "Ask" click to answer display |
| Query → Answer (complex, 5 chunks) | < 7 seconds | Same as above |
| Embedding generation (1 chunk) | < 500ms | Log OpenAI API latency |
| Vector search (top-5) | < 200ms | Log Upstash query latency |

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Unstructured.io API rate limits** | Medium | High | Cache parsed results; use local `unstructured` library fallback if API fails |
| **OpenAI API rate limits** | Low | High | Implement exponential backoff; monitor usage; use `gpt-3.5-turbo` fallback for dev |
| **Upstash free tier exceeded** | Low | Medium | Monitor query count; add warning at 8,000/10,000 daily limit |
| **Large PDF parsing timeout** | Medium | Medium | Set 60s timeout on Unstructured.io calls; show progress indicator to user |
| **Incorrect chunk metadata (bbox, page)** | Medium | Low | Log parsed elements for debugging; manual spot-checks during testing |
| **GPT hallucinates citations** | Medium | Medium | Validate `[chunk_id]` in answer matches retrieved chunks; Phase 3 adds confidence gate |
| **CORS issues (Next.js ↔ FastAPI)** | Low | Low | Configure FastAPI `CORSMiddleware` to allow `localhost:3000` |
| **Environment secrets leaked** | Low | High | Add `.env` to `.gitignore`; use `.env.example` template; document setup in README |

---

## 10. Dependencies & Prerequisites

### 10.1 External Services (Account Setup Required)

1. **Upstash** (https://console.upstash.com)
   - Create account (free tier)
   - Create Vector index: `nlp-doc-qa-dev` (Dense, 1536 dims, Cosine)
   - Copy `UPSTASH_VECTOR_REST_URL` and `UPSTASH_VECTOR_REST_TOKEN`

2. **OpenAI** (https://platform.openai.com)
   - Create account, add payment method (pay-as-you-go)
   - Generate API key with access to `gpt-5-mini` and `text-embedding-3-large`
   - Copy `OPENAI_API_KEY`

3. **Unstructured.io** (https://unstructured.io)
   - Sign up for API access (free tier: 1,000 pages/month)
   - Copy `UNSTRUCTURED_API_KEY` and `UNSTRUCTURED_API_URL`

### 10.2 Local Development Environment

- **Node.js:** v18+ (for Next.js)
- **Python:** 3.11+ (for FastAPI)
- **Package Managers:** npm (Node), pip (Python)
- **IDE:** VS Code recommended (with Python + ESLint extensions)
- **Git:** For version control

### 10.3 Environment Variables (`.env` Template)

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Upstash Vector
UPSTASH_VECTOR_REST_URL=https://...upstash.io
UPSTASH_VECTOR_REST_TOKEN=...

# Unstructured.io
UNSTRUCTURED_API_KEY=...
UNSTRUCTURED_API_URL=https://api.unstructured.io/general/v0/general

# FastAPI (optional, defaults to localhost:8000)
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Next.js (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 11. Verification & Sign-Off

Phase 1 is **complete** when the following checklist is satisfied:

- [ ] All success criteria (Section 2) met
- [ ] User stories (Section 4.1) manually tested and passing
- [ ] API contracts (Section 4.3) verified via Postman or curl
- [ ] UI components render correctly in Chrome, Firefox, Safari
- [ ] Performance benchmarks (Section 8.4) measured and documented
- [ ] No critical bugs (crashes, data loss, incorrect answers due to retrieval errors)
- [ ] Code committed to Git with clear commit messages
- [ ] README.md updated with setup instructions, environment variables, and screenshots
- [ ] Demo video recorded (2-3 minutes) showing upload → query → answer flow
- [ ] Handoff document drafted for Phase 2 (known limitations, TODOs, tech debt)

**Sign-Off Stakeholders:**
- Development Team Lead: [Name]
- Course Instructor: [Name] (optional demo/review)

---

## 12. Appendix

### 12.1 Sample `.env.example`

```bash
# Copy this file to .env and fill in your actual keys

# OpenAI API
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Upstash Vector Database
UPSTASH_VECTOR_REST_URL=https://xxxxx-xxxxx-xxxxx-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Unstructured.io API
UNSTRUCTURED_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
UNSTRUCTURED_API_URL=https://api.unstructured.io/general/v0/general

# FastAPI Config (optional, defaults shown)
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Next.js Config (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 12.2 Recommended Development Workflow

1. **Start FastAPI backend:**
   ```bash
   cd nextjs-fastapi
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   uvicorn api.index:app --reload --port 8000
   ```

2. **Start Next.js frontend (separate terminal):**
   ```bash
   cd nextjs-fastapi
   npm run dev
   ```

3. **Open browser:** `http://localhost:3000`

4. **Monitor logs:** FastAPI terminal shows backend logs; browser console shows frontend logs

5. **Iterate:** Edit code → save → auto-reload (FastAPI `--reload`, Next.js Fast Refresh)

### 12.3 Chunking Strategy Details

**Goal:** Preserve layout structure while keeping chunks semantically coherent and within token limits.

**Algorithm:**
1. Parse document with Unstructured.io → list of elements (paragraphs, tables, headings, etc.)
2. Group consecutive elements of the same type (e.g., consecutive paragraphs under same heading)
3. Split groups if total tokens > 512 (using `tiktoken` for gpt-5-mini tokenization)
4. For each chunk, attach metadata:
   - `doc_id`, `chunk_id` (sequential)
   - `page` (from element metadata)
   - `bbox` (average of all element bboxes in chunk, or first element's bbox)
   - `block_type` (majority type in chunk, e.g., "paragraph")
   - `section_heading` (most recent heading element above chunk)
   - `text` (concatenated element texts)

**Example:**
```
Elements:
1. Heading: "Section 3: Termination" (page 5)
2. Paragraph: "Either party may terminate..." (page 5, bbox [100, 200, 500, 250])
3. Paragraph: "Notice must be in writing..." (page 5, bbox [100, 260, 500, 310])

Chunk:
{
  "chunk_id": "chunk_23",
  "text": "Section 3: Termination\n\nEither party may terminate...\nNotice must be in writing...",
  "page": 5,
  "bbox": [100, 200, 500, 310],
  "block_type": "paragraph",
  "section_heading": "Section 3: Termination"
}
```

### 12.4 GPT Prompt Template (Full Version)

```python
def build_prompt(query: str, chunks: List[ChunkMetadata]) -> str:
    context_blocks = []
    for chunk in chunks:
        context_blocks.append(
            f"[{chunk.chunk_id}] "
            f"(Document: {chunk.doc_name}, Page {chunk.page}, Type: {chunk.block_type})\n"
            f"{chunk.text}\n"
        )
    
    context = "\n".join(context_blocks)
    
    prompt = f"""You are a helpful assistant answering questions about uploaded documents.

Context from documents:
{context}

User Question:
{query}

Instructions:
1. Answer the question using ONLY the information provided in the context above.
2. Cite your sources by including [chunk_id] inline in your answer wherever you reference information.
3. If the context does not contain enough information to answer the question, respond with: "I don't have enough information in the provided documents to answer this question."
4. Be concise, accurate, and professional.
5. Do not make up information or cite chunks that were not provided.

Answer:"""
    
    return prompt
```

### 12.5 References & Further Reading

- **Upstash Vector Docs:** https://upstash.com/docs/vector/overall/getstarted
- **OpenAI Embeddings Guide:** https://platform.openai.com/docs/guides/embeddings
- **Unstructured.io API Docs:** https://unstructured-io.github.io/unstructured/api.html
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Next.js 14 App Router:** https://nextjs.org/docs/app
- **Tailwind CSS:** https://tailwindcss.com/docs

---

**Document Status:** ✅ Final  
**Version:** 1.0  
**Last Updated:** 2026-01-22  
**Next Review:** Upon Phase 1 completion (transition to Phase 2 PRD)

