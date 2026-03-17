# Current State

This file is a factual snapshot of the document pipeline as currently implemented.

## Enforced Now

- Client-centric ingestion only
- No active generic `/api/v1/ai` or clientless extraction route
- Shared document processing service used by both API extraction and background worker
- Lean additive client intelligence schema present
- Read-only client intelligence suggestion service present
- Successful submit writes conservative confirmed outcomes back into the client intelligence layer
- Confirmed contact is explicitly represented in the draft/review/submit flow

## Suggestions

- Suggestions are client-scoped and contact-aware
- Suggestions are stored in `document_draft.draft_json["suggestions"]`
- Suggestions are explainable and deterministic
- Suggestions do not overwrite confirmed values automatically
- OCR supplier text, suggested contact, and confirmed contact are separate concepts

## Confirmed Contact Path

- Canonical draft field: `document_draft.confirmed_contact_id`
- Review payload field: `confirmed_contact_id`
- Confirmed contact must belong to the current client
- Intelligence write-back reads the explicit confirmed-contact path on successful submit
- Legacy `document_draft.counterparty_id` semantics are retired from the document subsystem

## Not Implemented Yet

- Autonomous or aggressive learning updates
- Approved-document table
- `document_repository` table
- Final posting boundary redesign
- Additional ingestion channels beyond current client-scoped upload flow
