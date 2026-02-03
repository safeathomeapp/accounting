# OCR / Document Review Readme

This file captures the current state of the document intake / OCR stub / document review feature so you can test it next session.

## Repo state (as of this session)

- Branch: `feat/doc-review-ui`
- No `AGENTS.md` found under `C:\Users\kevth\Desktop\Projects\Accountancy`

### What exists now

Backend (FastAPI + Postgres + Alembic):
- Models: `backend/models/document.py`
- Migration: `alembic/versions/v2_080_document_review_tables.py`
- API routes: `backend/api/documents_routes.py`
- Router mounted at `/api` in `backend/main.py`

Frontend (React + Vite + Tailwind):
- Page: `frontend/src/pages/DocumentReview.jsx`
- Route: `/documents/review` in `frontend/src/App.jsx`
- Navigation link: `frontend/src/components/Navigation.jsx`
- API client: `frontend/src/services/api.js`

Tests:
- `tests/test_documents_validation.py` (totals validation)

## Database schema (summary)

Tables are org-scoped for RLS readiness.

### `document_inbox_item`
- `org_id`, `uploaded_by_user_id`
- `source_type`, `file_name`, `mime_type`, `file_path`, `checksum_hash`
- `status`, `created_at`, `updated_at`

### `document_ocr_result`
- `inbox_item_id`, `org_id`
- `ocr_engine`, `raw_text`, `layout_json` (nullable), `pages`, `created_at`

### `document_draft`
- `inbox_item_id`, `org_id`
- guesses/confirmed fields: `doc_type`, `counterparty`, `doc_date`, `currency`, `invoice_no`, `totals`
- `draft_json`, `validation_json`
- `last_edited_by`, `submitted_by`, `status`, timestamps

### `document_draft_line`
- `draft_id`, `org_id`, `line_no`
- `description_guess/confirmed`
- `qty`, `unit_price`, `net`, `vat`, `gross`
- `vat_code_guess/confirmed`, `nominal_code_guess/confirmed`
- `confidence`

## API endpoints (current)

All are under `/api`:

- `POST /api/inbox/upload`
  - Stores file on disk (dev), creates `document_inbox_item`.
- `GET /api/inbox/{id}/file`
  - Streams the uploaded file from disk.
- `POST /api/inbox/{id}/extract`
  - Stub extraction: creates `document_ocr_result` and draft data.
  - Writes `document_draft` + `document_draft_line`.
  - Calculates validation issues and stores `validation_json`.
- `GET /api/drafts/{draft_id}`
  - Returns draft + lines + inbox item info.
- `PATCH /api/drafts/{draft_id}`
  - Saves edits, recalculates totals validation, updates lines.
- `POST /api/drafts/{draft_id}/submit`
  - Locks draft as `submitted`, stores validation JSON,
  - Creates/updates internal placeholder `Transaction` record.

## Frontend flow (current)

Route: `/documents/review`

Flow:
1) Upload a file (calls `/api/inbox/upload`)
2) Click “Run Extraction” (calls `/api/inbox/{id}/extract`)
3) Review/edit draft fields and lines
4) Save or Submit

Right pane includes:
- Header fields (doc type, counterparty, date, currency, invoice no, due date)
- Totals (net/vat/gross) + validation indicator
- Line items grid with VAT code + nominal code
- Actions: Save Draft, Submit

Left pane is a file preview iframe.

## Tests/build run in this session

- `python -m pytest tests/test_documents_validation.py -q`
- `npm run build` in `frontend/`

Note: Vite warns that `baseline-browser-mapping` data is 2+ months old. This is non-fatal.

## How to test next session

1) Apply migrations:
   - `alembic upgrade head`
2) Run backend:
   - `uvicorn backend.main:app --reload`
3) Run frontend:
   - `npm run dev` in `frontend/`
4) Go to `/documents/review`
5) Upload a PDF or image → Run Extraction → Review & Save/Submit

## Key files (for quick access)

- `backend/models/document.py`
- `alembic/versions/v2_080_document_review_tables.py`
- `backend/api/documents_routes.py`
- `backend/main.py`
- `frontend/src/pages/DocumentReview.jsx`
- `frontend/src/services/api.js`
- `frontend/src/App.jsx`
- `frontend/src/components/Navigation.jsx`
- `tests/test_documents_validation.py`
