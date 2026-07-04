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
    Migrations run automatically on launch.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection = None

    def initialize(self):
        """Create schema if not exists and run migrations."""
        logger.info(f"Initializing database at {self.db_path}")
        conn = self._get_connection()
        self._create_schema(conn)
        self._run_migrations(conn)
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
                archived    INTEGER NOT NULL DEFAULT 0,
                pinned      INTEGER NOT NULL DEFAULT 0,
                favorite    INTEGER NOT NULL DEFAULT 0,
                custom_title INTEGER NOT NULL DEFAULT 0,
                last_message TEXT DEFAULT '',
                message_count INTEGER NOT NULL DEFAULT 0
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
                access_count INTEGER NOT NULL DEFAULT 0,
                conversation_id TEXT DEFAULT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
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
                created_at  TEXT NOT NULL,
                conversation_id TEXT DEFAULT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv
                ON messages(conversation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_memories_importance
                ON memories(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_timeline_created
                ON execution_timeline(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_timeline_conv
                ON execution_timeline(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_memories_conv
                ON memories(conversation_id);
        """)
        conn.commit()

    def _column_exists(self, conn: sqlite3.Connection, table: str, column: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [row["name"] for row in cur.fetchall()]
        return column in cols

    def _run_migrations(self, conn: sqlite3.Connection):
        migrations_run = 0

        if not self._column_exists(conn, "conversations", "pinned"):
            conn.execute("ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
            migrations_run += 1
        if not self._column_exists(conn, "conversations", "favorite"):
            conn.execute("ALTER TABLE conversations ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0")
            migrations_run += 1
        if not self._column_exists(conn, "conversations", "custom_title"):
            conn.execute("ALTER TABLE conversations ADD COLUMN custom_title INTEGER NOT NULL DEFAULT 0")
            migrations_run += 1
        if not self._column_exists(conn, "conversations", "last_message"):
            conn.execute("ALTER TABLE conversations ADD COLUMN last_message TEXT DEFAULT ''")
            migrations_run += 1
        if not self._column_exists(conn, "conversations", "message_count"):
            conn.execute("ALTER TABLE conversations ADD COLUMN message_count INTEGER NOT NULL DEFAULT 0")
            migrations_run += 1
        if not self._column_exists(conn, "execution_timeline", "conversation_id"):
            conn.execute("ALTER TABLE execution_timeline ADD COLUMN conversation_id TEXT DEFAULT NULL")
            migrations_run += 1
        if not self._column_exists(conn, "memories", "conversation_id"):
            conn.execute("ALTER TABLE memories ADD COLUMN conversation_id TEXT DEFAULT NULL")
            migrations_run += 1

        if migrations_run:
            conn.commit()
            logger.info("Ran %d database migration(s)", migrations_run)

    # ── Conversations ─────────────────────────────────────────────────────

    def create_conversation(self, title: str, model: str = "llama3.2") -> dict:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO conversations "
                "(id, title, model, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, model, now, now),
            )
        return {"id": conv_id, "title": title, "model": model,
                "created_at": now, "updated_at": now,
                "last_message": "", "message_count": 0}

    def list_conversations(self) -> list[dict]:
        cur = self.execute(
            "SELECT id, title, model, created_at, updated_at, "
            "pinned, favorite, custom_title, last_message, message_count "
            "FROM conversations WHERE archived=0 "
            "ORDER BY pinned DESC, updated_at DESC LIMIT 200"
        )
        return [dict(row) for row in cur.fetchall()]

    def get_conversation(self, conv_id: str) -> dict | None:
        cur = self.execute(
            "SELECT id, title, model, created_at, updated_at, "
            "pinned, favorite, custom_title, last_message, message_count "
            "FROM conversations WHERE id=?", (conv_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def rename_conversation(self, conv_id: str, new_title: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, custom_title=1, updated_at=? "
                "WHERE id=?",
                (new_title, now, conv_id),
            )

    def set_conversation_title(self, conv_id: str, title: str):
        """Set title without marking as custom (used for auto-generation)."""
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                (title, now, conv_id),
            )

    def delete_conversation(self, conv_id: str):
        """Cascade delete conversation, messages, timeline events, and memory refs."""
        with self.transaction() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id=?", (conv_id,))
            conn.execute(
                "UPDATE memories SET conversation_id=NULL WHERE conversation_id=?",
                (conv_id,),
            )
            conn.execute(
                "DELETE FROM execution_timeline WHERE conversation_id=?",
                (conv_id,),
            )
            conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))

    def duplicate_conversation(self, conv_id: str, new_title: str,
                                new_conv_id: str = None) -> dict:
        """Duplicate a conversation and all its messages."""
        original = self.get_conversation(conv_id)
        if not original:
            return None
        new_id = new_conv_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO conversations "
                "(id, title, model, created_at, updated_at, last_message, message_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id, new_title, original["model"], now, now,
                 original.get("last_message", ""), original.get("message_count", 0)),
            )
            messages = self.get_messages(conv_id)
            for msg in messages:
                new_msg_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO messages "
                    "(id, conversation_id, role, content, created_at, token_count) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_msg_id, new_id, msg["role"], msg["content"],
                     msg["created_at"], msg.get("token_count", 0)),
                )
        return self.get_conversation(new_id)

    def update_last_message(self, conv_id: str, content: str):
        """Update the last_message preview and message_count."""
        now = datetime.now(timezone.utc).isoformat()
        preview = content.strip().replace("\n", " ")[:120]
        with self.transaction() as conn:
            conn.execute(
                "UPDATE conversations SET last_message=?, message_count=message_count+1, "
                "updated_at=? WHERE id=?",
                (preview, now, conv_id),
            )

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
        self.update_last_message(conv_id, content)
        return {"id": msg_id, "role": role, "content": content, "created_at": now}

    def get_messages(self, conv_id: str, limit: int = 200) -> list[dict]:
        cur = self.execute(
            "SELECT id, role, content, created_at, token_count FROM messages "
            "WHERE conversation_id=? ORDER BY created_at ASC LIMIT ?",
            (conv_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]

    def search_messages(self, conv_id: str, query: str) -> list[dict]:
        cur = self.execute(
            "SELECT id, role, content, created_at FROM messages "
            "WHERE conversation_id=? AND content LIKE ? "
            "ORDER BY created_at ASC LIMIT 50",
            (conv_id, f"%{query}%"),
        )
        return [dict(row) for row in cur.fetchall()]

    def search_conversations_by_content(self, query: str) -> list[dict]:
        """Search conversations where title or message content matches query."""
        cur = self.execute(
            """
            SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at,
                   c.last_message, c.message_count, c.pinned
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.archived=0
              AND (c.title LIKE ? OR m.content LIKE ?)
            ORDER BY c.updated_at DESC
            LIMIT 30
            """,
            (f"%{query}%", f"%{query}%"),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Search all conversations by title only ────────────────────────────

    def search_conversations_by_title(self, query: str) -> list[dict]:
        cur = self.execute(
            "SELECT id, title, created_at, updated_at, "
            "last_message, message_count, pinned "
            "FROM conversations WHERE archived=0 AND title LIKE ? "
            "ORDER BY updated_at DESC LIMIT 30",
            (f"%{query}%",),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Memories ──────────────────────────────────────────────────────────

    def add_memory(self, content: str, source: str = "conversation",
                   importance: float = 0.5, tags: list[str] = None,
                   conversation_id: str = None) -> dict:
        mem_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO memories (id, content, source, importance, "
                "created_at, accessed_at, conversation_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mem_id, content, source, importance, now, now, conversation_id),
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

    def get_conversation_memories(self, conv_id: str) -> list[dict]:
        cur = self.execute(
            "SELECT id, content, importance FROM memories "
            "WHERE conversation_id=? ORDER BY importance DESC",
            (conv_id,),
        )
        return [dict(row) for row in cur.fetchall()]

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
                           metadata: str = "{}",
                           conversation_id: str = None) -> dict:
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO execution_timeline (id, event_type, description, "
                "metadata, created_at, conversation_id) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, event_type, description, metadata, now, conversation_id),
            )
        return {"id": event_id, "type": event_type, "description": description}

    def get_timeline_events(self, limit: int = 100) -> list[dict]:
        cur = self.execute(
            "SELECT id, event_type, description, metadata, created_at "
            "FROM execution_timeline ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_conversation_timeline_events(self, conv_id: str) -> list[dict]:
        cur = self.execute(
            "SELECT id, event_type, description, metadata, created_at "
            "FROM execution_timeline WHERE conversation_id=? "
            "ORDER BY created_at ASC",
            (conv_id,),
        )
        return [dict(row) for row in cur.fetchall()]
