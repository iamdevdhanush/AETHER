"""
AETHER Memory Plugin
Manually manage long-term memories.
"""

import logging
from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class MemoryPlugin(PluginBase):
    """
    Exposes memory management as a plugin.
    Supports: list, add, delete, search, clear operations.
    """

    def initialize(self):
        self._db = None
        logger.info("Memory plugin initialized")

    def set_db(self, db):
        self._db = db

    async def execute(self, payload: dict) -> str:
        if self._db is None:
            return "Database not connected."

        action = payload.get("action", "list")
        text = payload.get("input", "").strip()

        if action == "list" or (not action and not text):
            return self._list_memories()
        elif action == "add" or text.startswith("add "):
            content = text.removeprefix("add ").strip() or payload.get("content", "")
            return self._add_memory(content)
        elif action == "search" or text.startswith("search "):
            query = text.removeprefix("search ").strip()
            return self._search_memories(query)
        elif action == "clear":
            return "Use the memory panel to clear all memories."
        else:
            # Default: treat as a search
            return self._search_memories(text)

    def _list_memories(self) -> str:
        memories = self._db.get_memories(limit=50)
        if not memories:
            return "No memories stored."
        lines = [f"Stored Memories ({len(memories)}):"]
        for i, mem in enumerate(memories, 1):
            importance = "⭐" * int(mem["importance"] * 5)
            lines.append(f"{i:2}. [{importance}] {mem['content'][:100]}")
        return "\n".join(lines)

    def _add_memory(self, content: str) -> str:
        if not content:
            return "No content to remember."
        mem = self._db.add_memory(content, source="manual", importance=0.8)
        return f"Remembered: {content[:80]}"

    def _search_memories(self, query: str) -> str:
        if not query:
            return self._list_memories()
        results = self._db.search_memories(query, limit=10)
        if not results:
            return f"No memories found for: {query}"
        lines = [f"Memories matching '{query}':"]
        for mem in results:
            lines.append(f"• {mem['content'][:120]}")
        return "\n".join(lines)

    def shutdown(self):
        logger.info("Memory plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "memory",
            "description": "Manage AETHER's long-term memory",
            "version": "1.0.0",
            "icon": "🧠",
            "category": "ai",
        }
