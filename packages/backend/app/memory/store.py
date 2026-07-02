import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.core.config import settings


class MemoryStore:
    def __init__(self):
        self.db_path = Path(settings.memory_db_path)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        await self._create_tables()

    async def _create_tables(self):
        async with self._lock:
            cursor = self._conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_memories_type
                    ON memories(type);
            """)
            self._conn.commit()

    async def save_conversation(self, conversation_id: str, title: str, messages: list[dict]) -> None:
        async with self._lock:
            now = datetime.now().timestamp()
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conversation_id, title, now, now),
            )
            for msg in messages:
                cursor.execute(
                    "INSERT OR REPLACE INTO messages (id, conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (msg["id"], conversation_id, msg["role"], msg["content"], msg.get("timestamp", now)),
                )
            self._conn.commit()

    async def get_conversations(self, limit: int = 20) -> list[dict]:
        async with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    async def get_conversation_messages(self, conversation_id: str) -> list[dict]:
        async with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    async def save_memory(self, content: str, memory_type: str = "conversation") -> str:
        import uuid
        memory_id = str(uuid.uuid4())
        async with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO memories (id, content, type, timestamp) VALUES (?, ?, ?, ?)",
                (memory_id, content, memory_type, datetime.now().timestamp()),
            )
            self._conn.commit()
        return memory_id

    async def search_memories(self, query: str, limit: int = 10) -> list[dict]:
        async with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{query}%", limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    async def close(self):
        if self._conn:
            self._conn.close()
