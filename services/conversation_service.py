"""
AETHER Conversation Service
Manages conversation lifecycle and message persistence.
"""

import logging
from typing import Optional

from database.db_manager import DatabaseManager
from services.ollama_service import OllamaService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Business logic layer for conversations.
    Wraps database operations and handles title generation.
    """

    def __init__(self, db: DatabaseManager, ollama: OllamaService,
                 memory: MemoryService):
        self.db = db
        self.ollama = ollama
        self.memory = memory

    async def create_conversation(self, title: str = "New Conversation",
                                   model: str = None) -> dict:
        """Create a new conversation and return its metadata."""
        model = model or self.ollama.current_model
        conv = self.db.create_conversation(title=title, model=model)
        logger.info(f"Created conversation {conv['id']}: {title}")
        return conv

    async def list_conversations(self) -> list[dict]:
        """Return all non-archived conversations, newest first."""
        return self.db.list_conversations()

    async def get_conversation(self, conv_id: str) -> Optional[dict]:
        return self.db.get_conversation(conv_id)

    async def delete_conversation(self, conv_id: str):
        self.db.delete_conversation(conv_id)
        logger.info(f"Deleted conversation {conv_id}")

    async def add_message(self, conversation_id: str, role: str,
                           content: str) -> dict:
        """Persist a message and optionally auto-generate title."""
        msg = self.db.add_message(conversation_id, role, content)

        # Generate a smart title from the first user message
        if role == "user":
            messages = self.db.get_messages(conversation_id)
            user_messages = [m for m in messages if m["role"] == "user"]
            if len(user_messages) == 1:
                title = await self._generate_title(content)
                self.db.update_conversation_title(conversation_id, title)

        return msg

    async def get_messages(self, conversation_id: str) -> list[dict]:
        """Return all messages for a conversation."""
        return self.db.get_messages(conversation_id)

    async def _generate_title(self, first_message: str) -> str:
        """Generate a short conversation title from the first message."""
        # Simple heuristic: first 50 chars of message, cleaned up
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        # Remove newlines
        title = title.replace("\n", " ").replace("\r", "")
        return title if title else "New Conversation"

    async def search_conversations(self, query: str) -> list[dict]:
        """Full-text search across conversation messages."""
        # SQLite LIKE search - sufficient for MVP
        cur = self.db.execute(
            """
            SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at
            FROM conversations c
            JOIN messages m ON m.conversation_id = c.id
            WHERE m.content LIKE ? AND c.archived = 0
            ORDER BY c.updated_at DESC
            LIMIT 20
            """,
            (f"%{query}%",),
        )
        return [dict(row) for row in cur.fetchall()]

    async def get_context_window(self, conversation_id: str,
                                  max_messages: int = 20) -> list[dict]:
        """
        Get the most recent messages for context.
        Ensures we don't exceed Ollama's context window.
        """
        messages = self.db.get_messages(conversation_id)
        return messages[-max_messages:]
