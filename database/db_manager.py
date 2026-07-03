"""
AETHER Database Manager
SQLite-based persistence for conversations, messages, memories, and settings.
"""

import logging
import sqlite3
import uuid
from pathlib import Path
import datetime
from datetime import datetime, timezone
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe SQLite database manager.
    All tables are created on first initialization.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection = None

    def initialize(self):
        """Create schema if not exists."""
        logger.info(f"Initializing database at {self.db_path}")
        conn = self._get_connection()
        self._create_schema(conn)
        logger.info("Database initialized")

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA synchronous=NORMAL")
        return self._connection

    @contextmanager
    def transaction(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        conn = self._get_connection()
        return conn.execute(sql, params)

    def executemany(self, sql: str, params_list) -> sqlite3.Cursor:
        conn = self._get_connection()
        return conn.executemany(sql, params_list)

    def commit(self):
        if self._connection:
            self._connection.commit()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def _create_schema(self, conn: sqlite3.Connection):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL DEFAULT 'New Conversation',
                model       TEXT NOT NULL DEFAULT 'llama3.2',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                archived    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id                  TEXT PRIMARY KEY,
                conversation_id     TEXT NOT NULL,
                role                TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content             TEXT NOT NULL,
                created_at          TEXT NOT NULL,
                token_count         INTEGER DEFAULT 0,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS memories (
                id          TEXT PRIMARY KEY,
                content     TEXT NOT NULL,
                source      TEXT NOT NULL DEFAULT 'conversation',
                importance  REAL NOT NULL DEFAULT 0.5,
                created_at  TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id   TEXT NOT NULL,
                tag         TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS plugin_data (
                plugin_name TEXT NOT NULL,
                key         TEXT NOT NULL,
                value       TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                PRIMARY KEY (plugin_name, key)
            );

            CREATE TABLE IF NOT EXISTS execution_timeline (
                id          TEXT PRIMARY KEY,
                event_type  TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata    TEXT DEFAULT '{}',
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv
                ON messages(conversation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_memories_importance
                ON memories(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_timeline_created
                ON execution_timeline(created_at DESC);
        """)
        conn.commit()
        logger.info("Schema created/verified")

    # ── Conversations ─────────────────────────────────────────────────────

    def create_conversation(self, title: str, model: str = "llama3.2") -> dict:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, model, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, model, now, now),
            )
        return {"id": conv_id, "title": title, "model": model, "created_at": now}

    def list_conversations(self) -> list[dict]:
        cur = self.execute(
            "SELECT id, title, model, created_at, updated_at FROM conversations "
            "WHERE archived=0 ORDER BY updated_at DESC LIMIT 100"
        )
        return [dict(row) for row in cur.fetchall()]

    def get_conversation(self, conv_id: str) -> dict | None:
        cur = self.execute(
            "SELECT * FROM conversations WHERE id=?", (conv_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def update_conversation_title(self, conv_id: str, title: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                (title, now, conv_id),
            )

    def delete_conversation(self, conv_id: str):
        with self.transaction() as conn:
            conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))

    def touch_conversation(self, conv_id: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at=? WHERE id=?",
                (now, conv_id),
            )

    # ── Messages ──────────────────────────────────────────────────────────

    def add_message(self, conv_id: str, role: str, content: str,
                    token_count: int = 0) -> dict:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, "
                "created_at, token_count) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, conv_id, role, content, now, token_count),
            )
        self.touch_conversation(conv_id)
        return {"id": msg_id, "role": role, "content": content, "created_at": now}

    def get_messages(self, conv_id: str, limit: int = 200) -> list[dict]:
        cur = self.execute(
            "SELECT id, role, content, created_at, token_count FROM messages "
            "WHERE conversation_id=? ORDER BY created_at ASC LIMIT ?",
            (conv_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Memories ──────────────────────────────────────────────────────────

    def add_memory(self, content: str, source: str = "conversation",
                   importance: float = 0.5, tags: list[str] = None) -> dict:
        mem_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO memories (id, content, source, importance, "
                "created_at, accessed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (mem_id, content, source, importance, now, now),
            )
            if tags:
                conn.executemany(
                    "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                    [(mem_id, t) for t in tags],
                )
        return {"id": mem_id, "content": content, "importance": importance}

    def get_memories(self, limit: int = 50) -> list[dict]:
        cur = self.execute(
            "SELECT id, content, source, importance, created_at, access_count "
            "FROM memories ORDER BY importance DESC, accessed_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def search_memories(self, query: str, limit: int = 10) -> list[dict]:
        cur = self.execute(
            "SELECT id, content, source, importance FROM memories "
            "WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        return [dict(row) for row in cur.fetchall()]

    def delete_memory(self, mem_id: str):
        with self.transaction() as conn:
            conn.execute("DELETE FROM memories WHERE id=?", (mem_id,))

    def touch_memory(self, mem_id: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "UPDATE memories SET accessed_at=?, access_count=access_count+1 "
                "WHERE id=?",
                (now, mem_id),
            )

    # ── Settings ──────────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        cur = self.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) "
                "VALUES (?, ?, ?)",
                (key, value, now),
            )

    # ── Plugin Data ───────────────────────────────────────────────────────

    def get_plugin_data(self, plugin: str, key: str, default: str = "") -> str:
        cur = self.execute(
            "SELECT value FROM plugin_data WHERE plugin_name=? AND key=?",
            (plugin, key),
        )
        row = cur.fetchone()
        return row["value"] if row else default

    def set_plugin_data(self, plugin: str, key: str, value: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plugin_data (plugin_name, key, value, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (plugin, key, value, now),
            )

    # ── Timeline ──────────────────────────────────────────────────────────

    def add_timeline_event(self, event_type: str, description: str,
                           metadata: str = "{}") -> dict:
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO execution_timeline (id, event_type, description, "
                "metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (event_id, event_type, description, metadata, now),
            )
        return {"id": event_id, "type": event_type, "description": description}

    def get_timeline_events(self, limit: int = 100) -> list[dict]:
        cur = self.execute(
            "SELECT id, event_type, description, metadata, created_at "
            "FROM execution_timeline ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
