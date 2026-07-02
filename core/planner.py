from __future__ import annotations
import uuid
import time
from typing import Optional
from models import ExecutionStep, StepStatus


class Planner:
    def __init__(self) -> None:
        self.steps: list[ExecutionStep] = []

    def plan(self, steps: list[dict]) -> list[ExecutionStep]:
        self.steps = [
            ExecutionStep(
                id=str(uuid.uuid4()),
                label=s.get("label", "Step"),
                status=StepStatus(s.get("status", "pending")),
                details=s.get("details"),
            )
            for s in steps
        ]
        return self.steps

    def update(self, step_id: str, status: StepStatus, details: Optional[str] = None) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                if details:
                    step.details = details
                break

    def clear(self) -> None:
        self.steps.clear()
