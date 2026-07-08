"""
AETHER Memory Service v2
Three memory layers:
  1. Short-term — current conversation buffer (in-memory)
  2. Working — current task context (in-memory)
  3. Long-term — persistent SQLite storage with summaries
"""

import logging
import re
import json
import time
from typing import Optional

from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MemoryService:

    def __init__(self, db: DatabaseManager, ollama=None):
        self.db = db
        self.ollama = ollama

        # Layer 1: Short-term (current conversation)
        self.short_term: list[dict] = []

        # Layer 2: Working (current task)
        self.working: dict = {
            "current_task": None,
            "task_goal": None,
            "task_steps": [],
            "current_step": 0,
            "artifacts": {},
        }

    # ── Layer 1: Short-term ──────────────────────────────────────────────

    def add_to_short_term(self, role: str, content: str) -> None:
        self.short_term.append({
            "role": role, "content": content, "timestamp": time.time(),
        })
        if len(self.short_term) > 50:
            self.short_term.pop(0)

    def get_short_term(self, limit: int = 20) -> list[dict]:
        return self.short_term[-limit:]

    def clear_short_term(self) -> None:
        self.short_term.clear()

    # ── Layer 2: Working memory ──────────────────────────────────────────

    def set_task(self, goal: str, steps: list[str]) -> None:
        self.working["current_task"] = goal
        self.working["task_goal"] = goal
        self.working["task_steps"] = steps
        self.working["current_step"] = 0
        self.working["artifacts"] = {}
        logger.info("Working memory: task set — %s", goal[:80])

    def update_task_progress(self, step_index: int) -> None:
        self.working["current_step"] = step_index

    def store_artifact(self, key: str, value: str) -> None:
        self.working["artifacts"][key] = value

    def get_working_context(self) -> str:
        w = self.working
        lines = []
        if w["current_task"]:
            lines.append(f"Current task: {w['current_task']}")
            lines.append(f"Progress: step {w['current_step']}/{len(w['task_steps'])}")
            if w["task_steps"]:
                for i, s in enumerate(w["task_steps"]):
                    marker = "→" if i == w["current_step"] else " " if i < w["current_step"] else " "
                    lines.append(f"  {marker} {i+1}. {s}")
            if w["artifacts"]:
                lines.append(f"Artifacts: {json.dumps(w['artifacts'], indent=2)}")
        return "\n".join(lines)

    def clear_working(self) -> None:
        self.working = {
            "current_task": None, "task_goal": None,
            "task_steps": [], "current_step": 0, "artifacts": {},
        }

    # ── Layer 3: Long-term (SQLite) ──────────────────────────────────────

    async def get_relevant_memories(self, query: str, limit: int = 8) -> list[dict]:
        words = [w.lower() for w in re.findall(r'\b\w{4,}\b', query)]
        if not words:
            return self.db.get_memories(limit=limit)[:limit]

        all_memories = self.db.get_memories(limit=200)
        scored = []
        for mem in all_memories:
            content_lower = mem["content"].lower()
            score = sum(1 for w in words if w in content_lower)
            if score > 0:
                scored.append((score, mem))
        scored.sort(key=lambda x: (-x[0], -x[1].get("importance", 0)))

        results = [m for _, m in scored[:limit]]
        for mem in results:
            self.db.touch_memory(mem["id"])
        return results or self.db.get_memories(limit=limit)

    async def get_all_memories(self) -> list[dict]:
        return self.db.get_memories(limit=200)

    async def add_memory(self, content: str, source: str = "agent",
                          importance: float = 0.7,
                          tags: list[str] = None) -> dict:
        return self.db.add_memory(content, source, importance, tags)

    async def delete_memory(self, memory_id: str):
        self.db.delete_memory(memory_id)

    async def store_workflow(self, goal: str, steps: list[dict],
                              result: str) -> None:
        summary = f"Workflow: {goal[:100]}"
        existing = self.db.search_memories(summary[:30], limit=3)
        if not any(summary.lower() in m["content"].lower() for m in existing):
            self.db.add_memory(
                content=summary,
                source="workflow",
                importance=0.9,
                tags=["workflow", *[s.get("tool", "") for s in steps]],
            )
            logger.info("Stored workflow memory: %s", summary[:60])

    async def remember_preference(self, key: str, value: str) -> None:
        content = f"Preference: {key} = {value}"
        existing = self.db.search_memories(content[:30], limit=3)
        if not any(content.lower() in m["content"].lower() for m in existing):
            self.db.add_memory(content=content, source="preference", importance=0.8)

    async def get_preference(self, key: str) -> Optional[str]:
        memories = self.db.get_memories(limit=100)
        for m in memories:
            match = re.match(rf"^Preference: {re.escape(key)}\s*=\s*(.+)$", m["content"])
            if match:
                return match.group(1)
        return None

    def _extract_name(self, text: str) -> str | None:
        patterns = [
            r"(?:my\s+(?:name\s+)?is|I'?m\s+called|call\s+me)\s+([A-Z]\w+)",
            r"(?:name'?s|name\s+is)\s+([A-Z]\w+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.I)
            if m:
                return m.group(1)
        return None

    async def extract_and_store(self, user_message: str,
                                 assistant_response: str):
        self.add_to_short_term("user", user_message)
        self.add_to_short_term("assistant", assistant_response)
        name = self._extract_name(user_message)
        if name:
            existing = self.db.search_memories(f"User's name is {name}", limit=2)
            if not any(name.lower() in m["content"].lower() for m in existing):
                self.db.add_memory(
                    content=f"User's name is {name}",
                    source="conversation", importance=0.9,
                    tags=["user_info", "name"],
                )

    async def summarize_and_store(self, conversation_id: str,
                                   messages: list[dict]) -> None:
        if len(messages) < 4:
            return
        if self.ollama:
            text = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in messages[-6:])
            try:
                summary = await self.ollama.summarize(text, max_length=200)
                if summary and len(summary) > 20:
                    existing = self.db.search_memories(summary[:30], limit=3)
                    if not any(summary.lower() in m["content"].lower() for m in existing):
                        self.db.add_memory(
                            content=f"Conversation summary: {summary}",
                            source="summary", importance=0.6,
                        )
            except Exception as e:
                logger.warning("Summarization failed: %s", e)
