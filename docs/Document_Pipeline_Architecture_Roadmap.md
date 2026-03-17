# Document Pipeline Architecture Roadmap

This document reflects the current implemented state first, then the next controlled steps. It is not a target-state schema dump.

## Implemented Now

- Generic and clientless AI/document routes have been removed.
- Client-scoped ingestion is the only canonical path.
- `document_inbox_item`, `document_ocr_result`, `document_draft`, and `document_draft_line` remain the operational document tables.
- Shared orchestration exists in `backend/services/document_processing.py` and is used by both the extraction API route and the worker.
- Lean client intelligence schema exists:
  - `client_intelligence_profile`
  - `client_supplier_alias`
  - `client_accounting_pattern`
  - `client_intelligence_event`
- Read-only client intelligence suggestions now exist via `backend/services/client_intelligence.py`.
- Conservative write-back from successful review submission now exists via `backend/services/client_intelligence_writeback.py`.
- Suggestions are client-scoped, contact-aware, explainable, and advisory only.
- Confirmed contact is now explicit in the draft/review/submit flow via a client-scoped contact reference.

## Explicitly Not Yet Implemented

- No `document_repository` table has been introduced.
- No approved-document table has been introduced.
- No autonomous learning, background rebuild, or aggressive write-back has been implemented.
- No automatic posting flow has been finalized.
- No additional ingestion channels such as email, WhatsApp, or Drive are implemented here.

## Current Canonical Lifecycle

Inbox item:
- `uploaded`
- `processing`
- `drafted`
- `submitted`
- `error`

Draft:
- `draft`
- `submitted`

The system currently leaves successful extracted items in `drafted` because the shared orchestration service creates or refreshes a review draft.

## Current Service Boundaries

`document_processing`
- loads the inbox item
- verifies client scope and file existence
- manages inbox status transitions
- runs OCR
- upserts `document_ocr_result`
- creates or refreshes `document_draft`
- preserves human-edited or submitted drafts

`client_intelligence`
- reads client intelligence profile if present
- matches supplier text against client-specific aliases
- falls back to exact normalized contact-name matching
- reads client accounting patterns
- builds explainable suggestion payloads
- records conservative reviewed outcomes on successful submit only
- appends audit events for successful learning and explicit skip cases

`documents_routes`
- remains the thin client-scoped API boundary
- preserves suggestion payloads when a draft is edited or submitted
- validates confirmed contact against the current client on review save and submit

## Review Boundary

- OCR is extraction evidence.
- Interpretation includes client-aware suggestions.
- Confirmed contact is explicit reviewer state, distinct from OCR text and suggestions.
- Suggestions do not become confirmed values automatically.
- Human review remains mandatory before submission.

## Next Controlled Steps

1. Decide the approved-document and posting boundary explicitly.
2. Harden review ergonomics around confidence and suggested-vs-confirmed visibility.
3. Add additional ingestion channels only as adapters into the same client-scoped inbox model.

## Non-Goals In The Current Repo State

- Reintroducing a generic AI extraction path
- Bypassing review with autonomous posting
- Creating a parallel non-client memory layer
- Introducing speculative repository tables before they are needed
