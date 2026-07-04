"""
AETHER Core Data Models
Shared types for the agent runtime pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Intent:
    type: str  # "tool" | "knowledge" | "chat" | "complex"
    tool_name: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    explanation: str = ""
    requires_planning: bool = False


@dataclass
class PlanStep:
    step_id: int
    description: str
    tool_name: str
    parameters: dict = field(default_factory=dict)
    status: str = "pending"  # pending | running | completed | failed | skipped
    observation: Optional[dict] = None
    reflection: Optional[str] = None


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    current_step: int = 0
    status: str = "created"  # created | running | completed | failed


@dataclass
class ReasoningState:
    thought: str = ""
    selected_tool: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    observation: Optional[dict] = None
    reflection: str = ""
    is_complete: bool = False
