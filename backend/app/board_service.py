from __future__ import annotations

import sqlite3
from pathlib import Path

from app.schemas import BoardPayload


DEFAULT_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog",
            "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress",
            "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


def validate_board_payload(board: BoardPayload) -> None:
    column_ids = [column.id for column in board.columns]
    if len(column_ids) != len(set(column_ids)):
        raise ValueError("Column ids must be unique.")

    seen_card_ids: set[str] = set()
    for column in board.columns:
        for card_id in column.card_ids:
            if card_id not in board.cards:
                raise ValueError(
                    f"Card '{card_id}' is referenced but missing from cards map.")
            if card_id in seen_card_ids:
                raise ValueError(
                    f"Card '{card_id}' appears in multiple columns.")
            seen_card_ids.add(card_id)

    if seen_card_ids != set(board.cards.keys()):
        raise ValueError(
            "Every card must appear exactly once in column cardIds.")


class BoardService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.executescript(
                """
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
                """
            )

    def get_board(self, username: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            board_id = self._ensure_user_board(conn, username)
            return self._read_board(conn, board_id)

    def save_board(self, username: str, board: BoardPayload) -> dict:
        validate_board_payload(board)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            board_id = self._ensure_user_board(conn, username)
            self._replace_board(conn, board_id, board)
            conn.commit()
            return self._read_board(conn, board_id)

    def _ensure_user_board(self, conn: sqlite3.Connection, username: str) -> int:
        user_row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user_row is None:
            cursor = conn.execute(
                "INSERT INTO users(username) VALUES (?)",
                (username,),
            )
            user_id = int(cursor.lastrowid)
        else:
            user_id = int(user_row["id"])

        board_row = conn.execute(
            "SELECT id FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if board_row is None:
            cursor = conn.execute(
                "INSERT INTO boards(user_id, name) VALUES (?, 'My Board')",
                (user_id,),
            )
            board_id = int(cursor.lastrowid)
            self._replace_board(
                conn, board_id, BoardPayload.model_validate(DEFAULT_BOARD))
            conn.commit()
            return board_id

        return int(board_row["id"])

    def _replace_board(self, conn: sqlite3.Connection, board_id: int, board: BoardPayload) -> None:
        conn.execute("DELETE FROM cards WHERE board_id = ?", (board_id,))
        conn.execute(
            "DELETE FROM board_columns WHERE board_id = ?", (board_id,))

        column_db_ids: dict[str, int] = {}
        for position, column in enumerate(board.columns):
            cursor = conn.execute(
                "INSERT INTO board_columns(board_id, key, title, position) VALUES (?, ?, ?, ?)",
                (board_id, column.id, column.title, position),
            )
            column_db_ids[column.id] = int(cursor.lastrowid)

        for column in board.columns:
            column_db_id = column_db_ids[column.id]
            for position, card_id in enumerate(column.card_ids):
                card = board.cards[card_id]
                conn.execute(
                    """
INSERT INTO cards(board_id, column_id, external_id, title, details, position)
VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (board_id, column_db_id, card.id,
                     card.title, card.details, position),
                )

    def _read_board(self, conn: sqlite3.Connection, board_id: int) -> dict:
        columns_rows = conn.execute(
            """
SELECT id, key, title
FROM board_columns
WHERE board_id = ?
ORDER BY position ASC
            """,
            (board_id,),
        ).fetchall()

        columns = []
        cards: dict[str, dict] = {}

        for column_row in columns_rows:
            column_cards_rows = conn.execute(
                """
SELECT external_id, title, details
FROM cards
WHERE board_id = ? AND column_id = ?
ORDER BY position ASC
                """,
                (board_id, int(column_row["id"])),
            ).fetchall()

            card_ids = []
            for card_row in column_cards_rows:
                card_id = str(card_row["external_id"])
                card_ids.append(card_id)
                cards[card_id] = {
                    "id": card_id,
                    "title": str(card_row["title"]),
                    "details": str(card_row["details"]),
                }

            columns.append(
                {
                    "id": str(column_row["key"]),
                    "title": str(column_row["title"]),
                    "cardIds": card_ids,
                }
            )

        return {"columns": columns, "cards": cards}
