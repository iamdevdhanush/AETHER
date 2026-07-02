from __future__ import annotations
import time
from typing import Optional
from models import ExecutionStep, StepStatus


class ExecutionTracker:
    def __init__(self) -> None:
        self.steps: list[ExecutionStep] = []

    def add_step(self, label: str, details: Optional[str] = None) -> ExecutionStep:
        import uuid
        step = ExecutionStep(
            id=str(uuid.uuid4()),
            label=label,
            status=StepStatus.pending,
            details=details,
        )
        self.steps.append(step)
        return step

    def update(self, step_id: str, status: StepStatus, details: Optional[str] = None) -> None:
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                if details is not None:
                    step.details = details
                break

    def clear(self) -> None:
        self.steps.clear()

    def to_list(self) -> list[dict]:
        return [
            {"id": s.id, "label": s.label, "status": s.status.value, "details": s.details}
            for s in self.steps
        ]
