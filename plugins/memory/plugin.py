"""
AETHER Memory Tool
Manage AETHER's long-term memory: list, add, search, delete.
"""

import logging
import time
from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class MemoryPlugin(ToolBase):

    def name(self) -> str:
        return "memory"

    def description(self) -> str:
        return "Manage AETHER's long-term memory: list, add, search, delete"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Action: list, add <text>, search <query>, delete <id>"},
                "action": {"type": "string", "enum": ["list", "add", "search", "delete"]},
                "content": {"type": "string", "description": "Content to remember"},
            },
        }

    def initialize(self):
        self._db = None

    def set_db(self, db):
        self._db = db

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        if self._db is None:
            return ToolObservation(stdout="", stderr="Database not connected.", exit_code=1, success=False)

        action = params.get("action", "")
        text = params.get("input", "").strip()

        if action == "list" or (not action and not text):
            result = self._list_memories()
        elif action == "add" or text.startswith("add "):
            content = text[4:].strip() if text.startswith("add ") else params.get("content", "")
            result = self._add_memory(content)
        elif action == "search" or text.startswith("search "):
            query = text[7:].strip() if text.startswith("search ") else text
            result = self._search_memories(query)
        else:
            result = self._search_memories(text)

        elapsed = (time.time() - start) * 1000
        return ToolObservation(stdout=result, exit_code=0, success=True, execution_time_ms=elapsed)

    def _list_memories(self) -> str:
        memories = self._db.get_memories(limit=50)
        if not memories:
            return "No memories stored."
        lines = [f"Stored Memories ({len(memories)}):"]
        for i, mem in enumerate(memories, 1):
            stars = "⭐" * int(mem["importance"] * 5)
            lines.append(f"{i:2}. [{stars}] {mem['content'][:100]}")
        return "\n".join(lines)

    def _add_memory(self, content: str) -> str:
        if not content:
            return "No content to remember."
        self._db.add_memory(content, source="manual", importance=0.8)
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
        logger.info("Memory tool shut down")
