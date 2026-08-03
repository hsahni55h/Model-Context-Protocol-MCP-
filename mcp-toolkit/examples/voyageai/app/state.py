"""Session state management with SQLite persistence.

Provides conversation history storage so users can continue
conversations across page reloads and maintain multiple sessions.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


class SessionStore:
    """SQLite-backed conversation state store."""

    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        self._conn.commit()

    def create_session(self) -> str:
        """Create a new conversation session.

        Returns:
            Unique session ID (UUID).
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, "", now, now),
        )
        self._conn.commit()
        return session_id

    def save_message(self, session_id: str, role: str, content: str) -> None:
        """Save a message to a session.

        Args:
            session_id: The session to save to.
            role: Message role ('user' or 'assistant').
            content: Message content.
        """
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        # Update session title from first user message
        if role == "user":
            existing_title = self._conn.execute(
                "SELECT title FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if existing_title and not existing_title[0]:
                title = content[:50] + ("..." if len(content) > 50 else "")
                self._conn.execute(
                    "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                    (title, now, session_id),
                )
        self._conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
        )
        self._conn.commit()

    def load_history(self, session_id: str) -> list[dict]:
        """Load conversation history for a session.

        Args:
            session_id: The session to load.

        Returns:
            List of message dicts with 'role' and 'content'.
        """
        rows = self._conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]

    def list_sessions(self) -> list[dict]:
        """List all sessions, most recent first.

        Returns:
            List of session dicts with 'id', 'title', 'created_at', 'updated_at'.
        """
        rows = self._conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {"id": row[0], "title": row[1], "created_at": row[2], "updated_at": row[3]}
            for row in rows
        ]

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages."""
        self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
