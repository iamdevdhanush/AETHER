"""
AETHER Observation Engine
Collects and structures observations after every tool execution.
Captures stdout, stderr, exit code, timing, screenshots, system changes.
"""

import logging
import time
from typing import Optional

from models.tool_base import ToolObservation

logger = logging.getLogger(__name__)


class ObservationEngine:

    def __init__(self):
        self._history: list[dict] = []

    async def observe(self, tool_name: str, params: dict,
                      tool_observation: ToolObservation) -> dict:
        entry = {
            "tool": tool_name,
            "params": params,
            "stdout": tool_observation.stdout,
            "stderr": tool_observation.stderr,
            "exit_code": tool_observation.exit_code,
            "execution_time_ms": tool_observation.execution_time_ms,
            "success": tool_observation.success,
            "screenshots": tool_observation.screenshots,
            "system_changes": tool_observation.system_changes,
            "metadata": tool_observation.metadata,
            "timestamp": time.time(),
        }
        self._history.append(entry)
        if len(self._history) > 200:
            self._history.pop(0)

        logger.info(
            "Observation: %s %s (%.0fms, exit=%d)",
            tool_name, "OK" if tool_observation.success else "FAIL",
            tool_observation.execution_time_ms, tool_observation.exit_code,
        )
        return entry

    def get_history(self, limit: int = 50) -> list[dict]:
        return self._history[-limit:]

    def get_last(self) -> Optional[dict]:
        return self._history[-1] if self._history else None

    def clear(self) -> None:
        self._history.clear()
