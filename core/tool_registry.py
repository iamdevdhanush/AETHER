"""
AETHER Tool Registry
Dynamic registry of all available tools.
Tools register themselves with name(), description(), parameters(), execute(), observe().
"""

import logging
from typing import Optional

from models.tool_base import ToolBase, ToolObservation
from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class LegacyPluginAdapter(ToolBase):
    """Wraps an old PluginBase instance as a ToolBase-compatible tool."""

    def __init__(self, plugin: PluginBase):
        self._plugin = plugin
        self._meta = plugin.metadata() if hasattr(plugin, 'metadata') else {}

    def name(self) -> str:
        return self._meta.get("name", type(self._plugin).__name__.lower().replace("plugin", ""))

    def description(self) -> str:
        return self._meta.get("description", f"Legacy plugin: {self.name()}")

    def parameters(self) -> dict:
        return {"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]}

    async def execute(self, params: dict) -> ToolObservation:
        import time
        start = time.time()
        try:
            result = await self._plugin.execute(params)
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout=str(result), exit_code=0, success=True, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=str(e), exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        if hasattr(self._plugin, 'shutdown'):
            self._plugin.shutdown()


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        name = tool.name()
        self._tools[name] = tool
        logger.info("Registered tool: %s — %s", name, tool.description())

    def get(self, name: str) -> Optional[ToolBase]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name(),
                "description": t.description(),
                "parameters": t.parameters(),
            }
            for t in self._tools.values()
        ]

    def find_by_capability(self, keywords: list[str]) -> list[tuple[str, float]]:
        scored = []
        for name, tool in self._tools.items():
            desc = tool.description().lower()
            score = sum(1 for kw in keywords if kw in desc or kw in name.lower())
            if score > 0:
                scored.append((name, score))
        scored.sort(key=lambda x: -x[1])
        return scored

    def shutdown_all(self) -> None:
        for name, tool in self._tools.items():
            try:
                tool.shutdown()
                logger.debug("Shut down tool: %s", name)
            except Exception as e:
                logger.error("Error shutting down tool %s: %s", name, e)
