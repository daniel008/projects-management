# Database Model Proposal (Part 5)

## Goals

- Use a normalized SQLite schema for users, boards, columns, cards, and ordering.
- Keep JSON usage limited to metadata and history payloads.
- Support MVP constraint of one board per user now, while preserving a clear path to multiple boards per user later.

## Schema Overview

### 1. users

Purpose: account identity (MVP currently uses dummy login, but DB supports future real users).

Columns:

- id INTEGER PRIMARY KEY
- username TEXT NOT NULL UNIQUE
- password_hash TEXT NULL
- created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Notes:

- `password_hash` can remain null during MVP if auth is not backend-enforced yet.

### 2. boards

Purpose: board container owned by a user.

Columns:

- id INTEGER PRIMARY KEY
- user_id INTEGER NOT NULL
- name TEXT NOT NULL DEFAULT 'My Board'
- created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Constraints:

- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- UNIQUE (user_id) for MVP one-board-per-user rule

Future:

- To allow multiple boards per user, remove the `UNIQUE (user_id)` constraint in a migration.

### 3. board_columns

Purpose: stores columns and board-level ordering.

Columns:

- id INTEGER PRIMARY KEY
- board_id INTEGER NOT NULL
- key TEXT NOT NULL
- title TEXT NOT NULL
- position INTEGER NOT NULL
- created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Constraints:

- FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
- UNIQUE (board_id, key)
- UNIQUE (board_id, position)

Notes:

- `key` is stable identity (e.g., `col-backlog`), while `title` is user-editable.

### 4. cards

Purpose: canonical task data and per-column ordering.

Columns:

- id INTEGER PRIMARY KEY
- board_id INTEGER NOT NULL
- column_id INTEGER NOT NULL
- external_id TEXT NOT NULL
- title TEXT NOT NULL
- details TEXT NOT NULL DEFAULT ''
- position INTEGER NOT NULL
- metadata_json TEXT NULL
- created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Constraints:

- FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
- FOREIGN KEY (column_id) REFERENCES board_columns(id) ON DELETE CASCADE
- UNIQUE (board_id, external_id)
- UNIQUE (column_id, position)

JSON usage:

- `metadata_json` contains optional card metadata only (labels, priority, due date hints, UI flags).

### 5. card_history

Purpose: append-only audit/history for card mutations.

Columns:

- id INTEGER PRIMARY KEY
- card_id INTEGER NOT NULL
- event_type TEXT NOT NULL
- payload_json TEXT NOT NULL
- created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Constraints:

- FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE

JSON usage:

- `payload_json` stores event payload (before/after snapshot fragments, move details, actor, source).

## Suggested DDL

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL DEFAULT 'My Board',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS board_columns (
  id INTEGER PRIMARY KEY,
  board_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  UNIQUE (board_id, key),
  UNIQUE (board_id, position)
);

CREATE TABLE IF NOT EXISTS cards (
  id INTEGER PRIMARY KEY,
  board_id INTEGER NOT NULL,
  column_id INTEGER NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  details TEXT NOT NULL DEFAULT '',
  position INTEGER NOT NULL,
  metadata_json TEXT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  FOREIGN KEY (column_id) REFERENCES board_columns(id) ON DELETE CASCADE,
  UNIQUE (board_id, external_id),
  UNIQUE (column_id, position)
);

CREATE TABLE IF NOT EXISTS card_history (
  id INTEGER PRIMARY KEY,
  card_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
CREATE INDEX IF NOT EXISTS idx_columns_board_id ON board_columns(board_id);
CREATE INDEX IF NOT EXISTS idx_cards_board_id ON cards(board_id);
CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
CREATE INDEX IF NOT EXISTS idx_history_card_id ON card_history(card_id);
```

## Bootstrap and Migration Approach

### Bootstrap from empty DB

At backend startup:

1. Ensure DB file path exists (create folder if needed).
2. Open SQLite connection.
3. Execute:
- `PRAGMA foreign_keys = ON;`
- `PRAGMA journal_mode = WAL;`
4. Run migration runner (idempotent SQL files in order).
5. If DB was empty, seed:
- default user row (or deferred if auth not yet wired),
- one board for that user,
- five default columns matching current frontend order.

### Migration tracking

Use a simple table:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  id INTEGER PRIMARY KEY,
  version TEXT NOT NULL UNIQUE,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

- Keep migration files in ascending order (`001_initial.sql`, `002_x.sql`, ...).
- Insert migration version into `schema_migrations` only after successful apply.

## Normalization Check (Review Checklist)

- User identity is stored once in `users`.
- Board ownership is stored once in `boards`.
- Column structure and order are in `board_columns`.
- Card canonical fields are in `cards`.
- Card event history is append-only in `card_history`.
- Ordering is normalized through integer `position` constraints, not array blobs.
- JSON appears only in `cards.metadata_json` and `card_history.payload_json`.

## Why This Fits MVP + Future

- Satisfies current one-board-per-user requirement with `UNIQUE (user_id)` on `boards`.
- Preserves future growth to multi-board by migrating that single unique constraint.
- Keeps high-frequency board reads straightforward with indexed joins.
- Avoids over-embedding data in JSON while still allowing flexible metadata/history payloads.
