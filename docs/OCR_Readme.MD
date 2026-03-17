# OCR / Document Review Readme

This file captures the current implemented document pipeline state on `feat/doc-review-ui`.

## Current Canonical Flow

- Client-centric ingestion only. There is no active generic `/api/v1/ai` or clientless document route.
- The canonical frontend route is `/client/:clientId/documents/review`.
- Upload creates a client-scoped `document_inbox_item`.
- Extraction runs through the shared backend orchestration service in `backend/services/document_processing.py`.
- OCR remains extraction-only. Interpretation now adds read-only client-aware suggestions from contacts and client intelligence where available.
- Successful submit now writes conservative confirmed outcomes back into the client intelligence layer.
- Confirmed counterparty resolution is explicit via a client-scoped confirmed contact path.
- Review is still mandatory. Nothing auto-posts to the ledger.

## Backend State

Implemented components:
- `backend/api/documents_routes.py`
  - `POST /api/inbox/upload`
  - `GET /api/inbox/{id}/file`
  - `POST /api/inbox/{id}/extract`
  - `GET /api/drafts/{draft_id}`
  - `PATCH /api/drafts/{draft_id}`
  - `POST /api/drafts/{draft_id}/submit`
- `backend/services/document_processing.py`
  - shared orchestration path for route and worker
  - owns inbox status transitions, OCR persistence, and draft persistence
- `backend/services/client_intelligence.py`
  - read-only contact alias and accounting-pattern lookup service
  - builds explainable suggestion payloads
- `backend/services/client_intelligence_writeback.py`
  - conservative write-back on successful submit only
  - upserts safe alias/pattern signals and appends audit events
- `backend/workers/process_documents.py`
  - background worker that calls the same shared processing service

## Data Flow

1. Upload stores the file and creates `document_inbox_item`.
2. Extraction loads the inbox item, verifies `client_id`, verifies file presence, and sets processing status.
3. OCR runs via the configured OCR service.
4. OCR evidence is stored in `document_ocr_result`.
5. A `document_draft` and `document_draft_line` set are created or refreshed.
6. Client-aware suggestions are attached to `draft_json["suggestions"]`.
7. User review confirms a client-scoped contact via `confirmed_contact_id` when appropriate.
8. User submission remains the decision point for confirmed values and conservative write-back.

## Suggestion Payload

Suggestions are stored in `document_draft.draft_json["suggestions"]` and are read-only in this pass.

Current shape:

```json
{
  "contact": {
    "suggested_id": "uuid-or-null",
    "suggested_name": "string-or-null",
    "confidence": "high|medium|low",
    "reasons": ["deterministic explanation"]
  },
  "nominal_account": {
    "suggested_id": "uuid-or-null",
    "suggested_code": "string-or-null",
    "suggested_name": "string-or-null",
    "confidence": "high|medium|low",
    "reasons": ["deterministic explanation"]
  },
  "document_type": {
    "suggested_value": "string-or-null",
    "confidence": "high|medium|low",
    "reasons": ["deterministic explanation"]
  },
  "tax_code": {
    "suggested_value": "string-or-null",
    "confidence": "high|medium|low",
    "reasons": ["deterministic explanation"]
  }
}
```

These suggestions do not overwrite confirmed values. They are advisory review inputs.

Confirmed contact is separate:
- OCR supplier text stays in the extracted draft path
- suggested contact stays in `draft_json["suggestions"]["contact"]`
- reviewer-confirmed contact is stored explicitly on the draft and submit payload
- legacy `counterparty_id` is no longer part of the active document review contract

## Matching Rules Implemented

- Exact normalized alias match in `client_supplier_alias`
- Exact normalized client contact-name fallback
- Read-only `client_accounting_pattern` lookup using matched contact and/or document type
- Fallback to no suggestion when there is no safe client-specific match

Successful submit now performs conservative, review-led write-back. It does not learn from OCR-only extraction or partial draft saves.

## Current Limitations

- No `document_repository` table exists.
- No approved-document table exists.
- No autonomous or aggressive learning exists.
- No automatic posting exists.
- Background processing and API extraction share orchestration, but suggestions remain advisory only.

## Key Files

- `backend/api/documents_routes.py`
- `backend/services/document_processing.py`
- `backend/services/client_intelligence.py`
- `backend/workers/process_documents.py`
- `backend/models/document.py`
- `backend/models/client_intelligence.py`
- `tests/test_document_processing_service.py`
- `tests/test_client_intelligence_service.py`
