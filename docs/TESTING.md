# Testing Guide - Phase 1

This document outlines manual testing procedures for the Intelligent Document Q&A System (Phase 1).

---

## Prerequisites

Before testing, ensure:
- ✅ Both servers running (`npm run dev`)
- ✅ `.env` configured with valid API keys
- ✅ Browser open to `http://localhost:3000`
- ✅ Test documents ready (see Test Documents section below)

---

## Test Suite

### Test 1: Initial Load & Empty State

**Objective:** Verify the application loads correctly when no documents are uploaded.

**Steps:**
1. Open `http://localhost:3000` in browser
2. Observe the page layout

**Expected Results:**
- ✅ Header displays "Intelligent Document Q&A System"
- ✅ Sidebar shows "0 uploaded" documents
- ✅ Main area shows "Get Started" section with upload zone
- ✅ No question input visible (requires documents first)
- ✅ No errors in browser console

---

### Test 2: Document Upload (Happy Path)

**Objective:** Successfully upload and index a PDF document.

**Test Document:** Use a simple 2-3 page PDF (contract, article, etc.)

**Steps:**
1. Click upload zone or drag & drop PDF
2. Wait for processing

**Expected Results:**
- ✅ Upload zone shows "Uploading and processing..." message
- ✅ After 10-15 seconds: Green success message appears
  - Shows filename, chunk count, page count
- ✅ Document appears in sidebar with:
  - Filename
  - Page count
  - Chunk count
  - "just now" timestamp
- ✅ Question input field becomes visible
- ✅ Upload zone moves to collapsible "Upload another document" section

**Console Check:**
- Backend logs show: parsing → chunking → embedding → upserting

---

### Test 3: Document Upload Error Handling

**Objective:** Validate error handling for invalid files.

**Sub-test 3a: Unsupported File Type**

**Steps:**
1. Try to upload a `.txt` file

**Expected Results:**
- ✅ Red error message: "Unsupported file type. Only .pdf, .png, .jpg, .jpeg, .docx allowed."
- ✅ No document added to sidebar

**Sub-test 3b: Very Large File** *(if file > 10MB available)*

**Steps:**
1. Upload a 15MB+ PDF

**Expected Results:**
- ✅ Backend returns 500 error
- ✅ Frontend shows error toast with message

---

### Test 4: Query with Simple Question

**Objective:** Generate an answer with citations for a straightforward query.

**Pre-requisite:** One document uploaded (e.g., employment contract)

**Steps:**
1. Type question: "What is the termination clause?"
2. Click "Ask"
3. Wait 3-5 seconds

**Expected Results:**
- ✅ "Ask" button shows spinning animation and "Thinking..."
- ✅ Answer appears with:
  - Clear answer text
  - One or more `[chunk_X]` citation tags inline
  - Query time displayed (e.g., "3.42s")
- ✅ Citations section shows expandable cards
- ✅ Each citation card displays:
  - Chunk ID (e.g., `chunk_23`)
  - Document name
  - Page number

**Console Check:**
- Backend logs: embedding query → vector search → GPT generation

---

### Test 5: Citation Expansion

**Objective:** Verify citation cards expand and display metadata.

**Pre-requisite:** Test 4 completed with answer displayed

**Steps:**
1. Click on any citation card header
2. Observe expanded content
3. Click "Copy text" button

**Expected Results:**
- ✅ Card expands smoothly
- ✅ Shows:
  - Full chunk text
  - Block type badge (e.g., "Type: paragraph")
  - Bounding box coordinates (if available)
- ✅ "Copy text" button copies text to clipboard
- ✅ Button changes to "✓ Copied!" briefly

---

### Test 6: Query with No Results

**Objective:** Handle queries about content not in documents.

**Pre-requisite:** Document uploaded (e.g., contract)

**Steps:**
1. Ask: "What is the recipe for chocolate cake?"
2. Wait for response

**Expected Results:**
- ✅ GPT returns something like:
  - "I don't have enough information in the provided documents to answer this question."
  - OR cites unrelated chunks (expected GPT behavior)
- ✅ No crashes or errors

---

### Test 7: Multiple Documents

**Objective:** Upload and query across multiple documents.

**Steps:**
1. Upload Document A (e.g., contract.pdf)
2. Upload Document B (e.g., manual.pdf)
3. Observe sidebar
4. Ask a question about Document B content

**Expected Results:**
- ✅ Sidebar shows both documents
- ✅ Most recent upload appears at top
- ✅ Query retrieves chunks from correct document
- ✅ Citations show correct `doc_name` field

---

### Test 8: Clear All Documents

**Objective:** Reset the system by deleting all documents.

**Pre-requisite:** 2+ documents uploaded

**Steps:**
1. Click "Clear All" button in sidebar
2. Observe UI changes

**Expected Results:**
- ✅ First click: Button text changes to "Click again to confirm" (red background)
- ✅ Second click (within 3 seconds):
  - All documents disappear from sidebar
  - Sidebar shows "0 uploaded"
  - Main area resets to "Get Started" upload zone
  - Previous answer/citations cleared
- ✅ If wait >3s after first click: Button reverts to "Clear All" (gray)

**Backend Check:**
- Vector store reset (all vectors deleted)

---

### Test 9: Refresh Document List

**Objective:** Re-fetch documents from backend.

**Steps:**
1. Upload a document
2. Click refresh icon (circular arrows) in sidebar header
3. Observe sidebar

**Expected Results:**
- ✅ Document list refreshes
- ✅ Same documents still visible
- ✅ No errors

*(This test is mainly for future multi-user scenarios)*

---

### Test 10: Responsive Layout

**Objective:** Verify UI adapts to different screen sizes.

**Steps:**
1. Resize browser window to ~800px width
2. Resize to ~500px width (mobile)
3. Return to full width

**Expected Results:**
- ✅ Sidebar remains visible and scrollable
- ✅ Main content area adjusts width
- ✅ Components remain readable
- ✅ No horizontal scroll
- ✅ Text wraps appropriately

---

### Test 11: Browser Compatibility

**Objective:** Ensure cross-browser functionality.

**Browsers to Test:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)

**Steps:**
1. Open app in each browser
2. Perform Tests 2, 4, 5

**Expected Results:**
- ✅ UI renders correctly in all browsers
- ✅ Upload works
- ✅ Query works
- ✅ Citations expand

---

### Test 12: API Error Recovery

**Objective:** Handle backend API failures gracefully.

**Sub-test 12a: Backend Offline**

**Steps:**
1. Stop FastAPI server (Ctrl+C)
2. Try to upload a document

**Expected Results:**
- ✅ Frontend shows error message
- ✅ No crashes
- ✅ Sidebar remains functional

**Sub-test 12b: Invalid API Key**

**Steps:**
1. Change `OPENAI_API_KEY` in `.env` to invalid value
2. Restart backend
3. Upload document → ask question

**Expected Results:**
- ✅ Upload may succeed (if parsing works)
- ✅ Query fails with error message
- ✅ Error logged in backend

---

## Test Documents (Recommended)

### Document A: Simple Contract (2-3 pages)
- **Purpose:** Basic upload and query testing
- **Content:** Employment contract with clauses, dates, signatures
- **Test Queries:**
  - "What is the termination clause?"
  - "What is the salary mentioned?"
  - "Who are the parties to this agreement?"

### Document B: Multi-page Manual (5-10 pages)
- **Purpose:** Chunking and layout testing
- **Content:** User manual with sections, tables, diagrams
- **Test Queries:**
  - "How do I reset the device?"
  - "What is the warranty period?"
  - "What are the technical specifications?"

### Document C: Image (Scanned PDF or PNG)
- **Purpose:** OCR testing
- **Content:** Scanned document (invoice, receipt, form)
- **Test Queries:**
  - "What is the total amount?"
  - "What is the date on this document?"

---

## Performance Benchmarks

Run these tests and record results:

| Test | Metric | Target | Actual |
|------|--------|--------|--------|
| Upload 10-page PDF | Time to indexed | < 15s | ______ |
| Simple query | Time to answer | < 5s | ______ |
| Complex query (5 chunks) | Time to answer | < 7s | ______ |
| Sidebar refresh | Latency | < 500ms | ______ |

---

## Edge Cases to Test

1. **Empty document**: Upload a blank PDF
   - Expected: Parsing may fail or return 0 chunks

2. **Document with only images**: Upload image-heavy PDF
   - Expected: OCR extracts text (may be limited)

3. **Very long query**: Type 500+ word question
   - Expected: Works but answer may be generic

4. **Rapid uploads**: Upload 3 docs in quick succession
   - Expected: All process correctly (may queue)

5. **Special characters in filename**: Upload `test-doc (2024).pdf`
   - Expected: Filename preserved, no errors

---

## Bug Tracking Template

When you find a bug, document it:

```markdown
## Bug: [Short description]

**Severity:** Critical / High / Medium / Low

**Steps to Reproduce:**
1. ...
2. ...
3. ...

**Expected Behavior:**
...

**Actual Behavior:**
...

**Screenshots/Logs:**
...

**Environment:**
- Browser: Chrome 120.0.6099
- OS: macOS 14.0
- Backend: Running on localhost:8000
```

---

## Test Completion Checklist

- [ ] All 12 tests completed
- [ ] Edge cases tested
- [ ] Performance benchmarks recorded
- [ ] No critical bugs found (or all logged)
- [ ] Cross-browser testing done
- [ ] README tested for accuracy

---

**Status:** Ready for Phase 1 Review  
**Last Updated:** 2025-01-22

