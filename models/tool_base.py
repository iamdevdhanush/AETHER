"""
AETHER Tool Base
Every tool must implement this interface.
Tools are the atomic unit of capability in AETHER.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class ToolObservation:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0
    success: bool = True
    screenshots: list[str] = field(default_factory=list)
    system_changes: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def summary(self) -> str:
        if self.success:
            return self.stdout[:500] if self.stdout else "(completed)"
        return f"Failed (exit {self.exit_code}): {self.stderr[:300]}"


class ToolBase(ABC):

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def parameters(self) -> dict:
        """
        Return JSON schema for this tool's parameters.
        Example: {"type": "object", "properties": {"path": {"type": "string"}}}
        """

    def can_execute(self, params: dict) -> bool:
        return True

    @abstractmethod
    async def execute(self, params: dict) -> ToolObservation: ...

    def observe(self, result: ToolObservation) -> ToolObservation:
        return result

    def shutdown(self) -> None: ...
