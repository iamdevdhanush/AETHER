from __future__ import annotations
import time
import uuid
from typing import Optional
from services.database import MemoryStore
from models import Memory


class MemoryManager:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    async def save(self, content: str, memory_type: str = "conversation") -> str | None:
        if not self._enabled:
            return None
        return await self.store.save_memory(content, memory_type)

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if not self._enabled:
            return []
        return await self.store.search_memories(query, limit)

    async def get_recent(self, limit: int = 20) -> list[Memory]:
        results = await self.store.search_memories("", limit)
        return [
            Memory(id=r["id"], content=r["content"], type=r["type"], timestamp=r["timestamp"])
            for r in results
        ]
