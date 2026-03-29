# Project Plan

## Decisions Confirmed

- [x] Keep this document as the canonical phased plan and enrich it with implementation checklists.
- [x] Create and maintain `frontend/AGENTS.md`, including frontend testing guidance.
- [x] Keep Part 2 hello-world static and API smoke behavior for now.
- [x] Use multi-service Docker Compose for local MVP.
- [x] Use frontend-only session state for fake auth in Part 4.
- [x] Use normalized SQLite tables, with JSON used only for card metadata/history.
- [x] Use permissive structured-output parsing from AI, with explicit fallback behavior.
- [x] Testing quality bar: minimum 80% unit coverage plus robust integration testing.

## Global Standards

- [ ] Keep implementation simple and avoid over-engineering.
- [ ] Use latest stable idiomatic libraries/framework patterns at implementation time.
- [ ] Prove root cause before applying fixes when issues are found.
- [ ] Keep docs concise and scoped to MVP decisions.
- [ ] Ensure each completed part has matching tests and explicit acceptance checks.

## Test Strategy (Applies Across Parts)

- [ ] Unit tests target 80%+ coverage for code introduced in each phase.
- [ ] Integration tests cover key cross-boundary paths (frontend and backend interactions).
- [ ] E2E smoke tests cover critical user journeys at each major milestone.
- [ ] CI/local test commands are documented and reproducible.
- [ ] Defect fixes include regression tests where practical.

## Part 1: Plan and Documentation

### Scope

- [x] Enrich this plan with detailed execution checklists, tests, and success criteria for Parts 2-10.
- [x] Create `frontend/AGENTS.md` documenting existing frontend architecture, behavior, and tests.
- [x] Share plan for user approval before implementation work begins.

### Tests

- [x] Manual review confirms all requested decisions are captured.
- [x] Manual review confirms each part contains checklist, tests, and success criteria.

### Success Criteria

- [x] User explicitly approves plan and frontend agent documentation.

## Part 2: Scaffolding (Docker + Backend Skeleton)

### Scope

- [x] Add multi-service Docker Compose for local development.
- [x] Create FastAPI backend skeleton in `backend/`.
- [x] Add scripts for start/stop on Mac, Windows, and Linux under `scripts/`.
- [x] Serve example static hello-world HTML and example API endpoint.
- [x] Keep smoke endpoints in place for now.

### Tests

- [x] Backend unit tests for health/smoke API behavior.
- [x] Integration test proving compose services boot and API is reachable.
- [x] Script-level smoke test: start script boots services and stop script shuts them down cleanly.

### Success Criteria

- [x] `docker compose up` starts all services without manual patching.
- [x] Browser returns hello-world page from backend static route.
- [x] Example API call returns expected payload.

## Part 3: Serve Frontend Through Backend

### Scope

- [ ] Build existing Next.js frontend as static output.
- [ ] Configure backend to serve built frontend at `/`.
- [ ] Preserve current Kanban demo functionality in served build.

### Tests

- [ ] Frontend unit tests pass with 80%+ coverage.
- [ ] Integration test verifies backend serves frontend files and app shell.
- [ ] E2E test verifies `/` renders Kanban board with expected columns.

### Success Criteria

- [ ] Visiting `/` from running stack shows current Kanban UI.
- [ ] No runtime dependency on standalone `next dev` in integrated mode.

## Part 4: Fake User Sign-In (Frontend Session State)

### Scope

- [ ] Add login gate at `/` with hardcoded credentials `user` and `password`.
- [ ] Implement frontend-only session state to control logged-in view.
- [ ] Add logout action that clears session state and returns to login form.

### Tests

- [ ] Unit tests for login form validation and session state transitions.
- [ ] Integration tests for login success, login failure, and logout.
- [ ] E2E test for full login-to-kanban and logout-to-login journey.

### Success Criteria

- [ ] Unauthenticated users cannot see board content.
- [ ] Correct credentials reveal board; logout reliably hides it again.

## Part 5: Database Modeling (Normalized + JSON Metadata/History)

### Scope

- [ ] Propose normalized SQLite schema for users, boards, columns, cards, and ordering.
- [ ] Include JSON fields only where useful (card metadata/history, optional audit payloads).
- [ ] Document schema and migration/bootstrap approach in `docs/`.
- [ ] Request and obtain explicit user sign-off before implementation.

### Tests

- [ ] Schema review checklist verifies normalization and constraint coverage.
- [ ] Migration/bootstrap test creates DB from empty state without errors.

### Success Criteria

- [ ] Approved schema document is committed in `docs/`.
- [ ] Data model supports one board per user now and multi-user growth later.

## Part 6: Backend Kanban API + Persistence

### Scope

- [ ] Implement DB initialization if database file does not exist.
- [ ] Add API routes for reading/updating Kanban state for a given user.
- [ ] Enforce ordering and data integrity at API/service layer.

### Tests

- [ ] Unit tests for service-layer transformations and validation logic (80%+).
- [ ] Integration tests for API CRUD flows and persistence behavior.
- [ ] Negative-path tests for invalid IDs/payloads.

### Success Criteria

- [ ] API persists and returns consistent board state across process restarts.
- [ ] API behavior is deterministic and covered by tests.

## Part 7: Frontend + Backend Integration

### Scope

- [ ] Replace in-memory frontend board state with backend API integration.
- [ ] Keep drag/drop, rename, add, delete behavior while persisting updates.
- [ ] Add loading/error states for network operations.

### Tests

- [ ] Unit tests for client data adapters/state transitions (80%+).
- [ ] Integration tests using mocked or test backend endpoints.
- [ ] E2E tests verifying persisted updates survive page refresh.

### Success Criteria

- [ ] All core Kanban actions persist through backend and reload correctly.
- [ ] App remains responsive with clear error handling when API fails.

## Part 8: AI Connectivity via OpenRouter

### Scope

- [ ] Add backend AI client using OpenRouter and `.env` key.
- [ ] Configure model `openai/gpt-oss-120b`.
- [ ] Implement initial connectivity path (simple "2+2" style verification route or service test).

### Tests

- [ ] Unit tests for AI client configuration and request composition (mocked).
- [ ] Integration test with mocked OpenRouter response path.
- [ ] Optional manual live connectivity check gated on key availability.

### Success Criteria

- [ ] Backend can successfully execute and parse a basic AI request/response cycle.

## Part 9: Structured Outputs for Chat + Board Updates

### Scope

- [ ] Send full board JSON, user question, and conversation history to AI endpoint.
- [ ] Define structured response contract with fields for user message and optional board patch/update.
- [ ] Implement permissive parsing with fallback behavior when response is malformed/partial.
- [ ] Apply validated board updates server-side before returning response.

### Tests

- [ ] Unit tests for prompt payload shaping and parser behavior (valid/partial/invalid cases).
- [ ] Integration tests for backend endpoint applying AI-suggested board updates.
- [ ] Regression tests for fallback path when model output does not match expected schema.

### Success Criteria

- [ ] User always receives a chat response even on schema mismatch.
- [ ] Valid AI board updates are safely applied and persisted.

## Part 10: Frontend AI Sidebar + Live Board Refresh

### Scope

- [ ] Add sidebar chat UI integrated with backend AI endpoint.
- [ ] Render conversation history and request status.
- [ ] Reflect AI-driven board updates in UI immediately after successful response.

### Tests

- [ ] Unit tests for chat UI state management and message rendering (80%+).
- [ ] Integration tests for chat request lifecycle and board refresh trigger.
- [ ] E2E tests for end-to-end chat interaction that results in board mutation.

### Success Criteria

- [ ] Chat sidebar is usable and stable in desktop and mobile layouts.
- [ ] Board visibly refreshes when AI returns update instructions.
- [ ] Critical user journeys pass E2E checks.