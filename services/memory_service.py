"""
AETHER Memory Service
Extracts, stores, and retrieves persistent memories from conversations.
"""

import logging
import re
from typing import Optional

from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Patterns that suggest something worth remembering
MEMORY_PATTERNS = [
    r"my name is (.+)",
    r"i am (.+)",
    r"i work (at|for|as) (.+)",
    r"i live in (.+)",
    r"i prefer (.+)",
    r"i like (.+)",
    r"i use (.+)",
    r"remember that (.+)",
    r"don't forget (.+)",
    r"my (.+) is (.+)",
    r"i'm (.+)",
]


class MemoryService:
    """
    Manages long-term memory storage and retrieval.
    Memories are extracted from conversations and used as context in future chats.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._patterns = [re.compile(p, re.IGNORECASE) for p in MEMORY_PATTERNS]

    async def get_relevant_memories(self, query: str,
                                     limit: int = 8) -> list[dict]:
        """
        Retrieve memories relevant to the current query.
        Uses keyword matching against stored memories.
        """
        # Extract meaningful keywords from query (words > 3 chars)
        words = [w.lower() for w in re.findall(r'\b\w{4,}\b', query)]

        if not words:
            return self.db.get_memories(limit=limit)[:limit]

        # Score memories by keyword matches
        all_memories = self.db.get_memories(limit=200)
        scored = []
        for mem in all_memories:
            content_lower = mem["content"].lower()
            score = sum(1 for w in words if w in content_lower)
            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: (-x[0], -x[1].get("importance", 0)))

        # Update access stats for retrieved memories
        results = [m for _, m in scored[:limit]]
        for mem in results:
            self.db.touch_memory(mem["id"])

        # Fall back to most important memories if no matches
        if not results:
            results = self.db.get_memories(limit=limit)

        return results

    async def get_all_memories(self) -> list[dict]:
        """Return all memories for display in the memory panel."""
        return self.db.get_memories(limit=200)

    async def add_memory(self, content: str, source: str = "manual",
                          importance: float = 0.7,
                          tags: list[str] = None) -> dict:
        """Manually add a memory."""
        return self.db.add_memory(content, source, importance, tags)

    async def delete_memory(self, memory_id: str):
        """Delete a memory by ID."""
        self.db.delete_memory(memory_id)
        logger.info(f"Deleted memory {memory_id}")

    async def extract_and_store(self, user_message: str,
                                 assistant_response: str):
        """
        Analyze conversation exchange and extract memorable facts.
        Called after each AI response.
        """
        extracted = self._extract_from_text(user_message)
        for content, importance in extracted:
            # Check for duplicate before storing
            existing = self.db.search_memories(content[:30], limit=5)
            if not any(
                content.lower() in m["content"].lower() for m in existing
            ):
                self.db.add_memory(
                    content=content,
                    source="conversation",
                    importance=importance,
                )
                logger.debug(f"Stored memory: {content[:60]}")

    def _extract_from_text(self, text: str) -> list[tuple[str, float]]:
        """
        Extract memorable statements from text.
        Returns list of (content, importance) tuples.
        """
        results = []
        text_lower = text.lower().strip()

        for pattern in self._patterns:
            match = pattern.search(text_lower)
            if match:
                # Reconstruct with original casing from matched position
                start = match.start()
                end = match.end()
                content = text[start:end].strip()
                if len(content) > 5 and len(content) < 200:
                    importance = 0.8 if "remember" in text_lower else 0.6
                    results.append((content, importance))

        return results

    async def update_importance(self, memory_id: str, importance: float):
        """Update the importance score of a memory."""
        now_str = __import__("datetime").datetime.utcnow().isoformat()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE memories SET importance=? WHERE id=?",
                (max(0.0, min(1.0, importance)), memory_id),
            )

    async def search_memories(self, query: str) -> list[dict]:
        """Search memories by content."""
        return self.db.search_memories(query)
