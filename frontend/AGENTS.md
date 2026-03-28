# Frontend Agent Notes

## Purpose

The `frontend/` workspace currently provides a standalone Next.js Kanban demo app. It is the starting point that will later be statically built and served by the FastAPI backend.

## Stack

- Framework: Next.js 16 (App Router), React 19, TypeScript
- Styling: Tailwind CSS v4 with custom variables in `src/app/globals.css`
- Drag and drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- Unit/component testing: Vitest, Testing Library, jsdom
- E2E testing: Playwright (Chromium)

## Current App Structure

- Entry route: `src/app/page.tsx` renders `KanbanBoard`.
- Root layout: `src/app/layout.tsx` configures metadata and fonts.
- Global styles: `src/app/globals.css` defines design tokens and base styles.

### Components

- `src/components/KanbanBoard.tsx`: owns in-memory board state and drag context; handles rename, add, delete, and move actions.
- `src/components/KanbanColumn.tsx`: droppable column with editable title, sortable card list, and new-card form.
- `src/components/KanbanCard.tsx`: draggable sortable card with delete action.
- `src/components/KanbanCardPreview.tsx`: drag overlay preview.
- `src/components/NewCardForm.tsx`: inline form for creating new cards.

### Domain Helpers

- `src/lib/kanban.ts`: board/card/column types, seed data, move algorithm, and ID generation helper.

## Current Behavior

- Single-board Kanban with five seeded columns.
- Inline column title editing.
- Card creation and deletion.
- Drag-and-drop reorder within a column and move across columns.
- State is in-memory only; no backend persistence yet.

## Frontend Commands

Run from `frontend/`:

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`
- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:all`

## Testing Details

- Vitest config: `vitest.config.ts`
- Unit environment: `jsdom`
- Unit setup file: `src/test/setup.ts`
- Unit test include pattern: `src/**/*.{test,spec}.{ts,tsx}`
- Unit coverage reporter: text and html

Current unit tests:

- `src/lib/kanban.test.ts`: `moveCard` reorder/move/append behavior
- `src/components/KanbanBoard.test.tsx`: board render, column rename, add/remove card flow

Current E2E tests:

- `tests/kanban.spec.ts`: board load, add-card flow, drag-and-drop between columns

## Standards for Upcoming Work

- Keep implementation simple and within MVP scope.
- Preserve the existing visual token system in `globals.css`.
- Add tests whenever behavior changes.
- Maintain at least 80% unit coverage for frontend code changed in each phase.
- Favor robust integration assertions over brittle cosmetic assertions.

## Known Constraints

- Frontend currently runs standalone and is not yet served by the backend.
- No auth flow yet (planned fake login phase).
- No AI sidebar yet (planned later phase).
