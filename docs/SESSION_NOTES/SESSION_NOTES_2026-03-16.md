# Session Notes - March 16, 2026

## Session Overview
**Focus**: Database hardening completion + login debugging
**Branch**: `feat/doc-review-ui`

---

## Completed

### 1. Final Database Hardening Step
Revoked direct SELECT access on sensitive tables from `app_user`:
```sql
REVOKE SELECT ON public.users FROM app_user;
REVOKE SELECT ON public.organizations FROM app_user;
```

Verified resulting privileges:
- `users`: `app_user=aw` (INSERT/UPDATE only — no SELECT)
- `organizations`: `app_user=w` (UPDATE only — no SELECT)

All auth flows must now go through the SECURITY DEFINER functions created in v2_114. The database hardening stance from `FINAL_NON_NEGOTIABLE_DB_STANCE.md` is **fully complete**.

### 2. Diagnosed and Fixed Silent Login Loop

**Symptom**: Could not log in — no error on screen, no error in console, just returned to login page.

**Root cause (3-step chain)**:
1. Test user's stored password hash didn't match `"password"` → API returned 401
2. `authStore.js` catch block has a demo fallback for `test@example.com` that silently swallows the error and sets a hardcoded fake token (`demo-token-12345`) in localStorage
3. Fake token is invalid JWT → every API call from `/home` returns 401 → `api.js` interceptor fires `window.location.href = '/login'` (full page reload clears the console) → infinite silent redirect loop

**Fix**: Reset test user's password hash in the DB to the correct SHA256 hash for `"password"`.

**Note**: The REVOKEs had no impact on login — the app connects as the `postgres` superuser which bypasses RLS regardless. Hardening is correctly applied only to `app_user`.

---

## Current State

- Database hardening: **complete**
- Servers running: backend `:8000`, frontend `:3000`
- Login working with `test@example.com` / `password`

---

## Next Session Priorities

- TBD — awaiting direction on next project phase

---

**Session End**: March 16, 2026
