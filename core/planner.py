"""
AETHER Planner
Decomposes complex requests into structured, actionable steps.
Outputs a Plan with ordered PlanSteps, each referencing a tool + parameters.
"""

import logging
import json
from typing import Optional

from core.models import Plan, PlanStep
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class Planner:

    def __init__(self, tool_registry: ToolRegistry, ollama=None):
        self.tool_registry = tool_registry
        self.ollama = ollama

    async def create_plan(self, goal: str) -> Plan:
        plan = Plan(goal=goal)

        if self.ollama:
            try:
                steps = await self._llm_decompose(goal)
            except Exception as e:
                logger.warning("LLM planning failed: %s", e)
                steps = self._default_steps(goal)
        else:
            steps = self._default_steps(goal)

        for i, step_data in enumerate(steps):
            plan.steps.append(
                PlanStep(
                    step_id=i + 1,
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool", ""),
                    parameters=step_data.get("parameters", {}),
                )
            )

        logger.info("Created plan with %d steps for: %s", len(plan.steps), goal[:80])
        return plan

    async def _llm_decompose(self, goal: str) -> list[dict]:
        tools_desc = "\n".join(
            f"  - {t['name']}: {t['description']}"
            for t in self.tool_registry.list_tools()
        )

        prompt = (
            f"Break this request into sequential steps using available tools:\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            f"Request: \"{goal}\"\n\n"
            f"Return a JSON array of steps. Each step: {{\n"
            f'  "description": "what to do",\n'
            f'  "tool": "tool_name",\n'
            f'  "parameters": {{"input": "..."}}\n'
            f"}}\n\n"
            f"Example:\n"
            f'[{{\"description\": "Open VS Code", "tool": "vscode", "parameters": {{"input": "/project"}}}}, {{\"description\": "Pull latest git changes", "tool": "git", "parameters": {{"input": "pull"}}}}]\n\n'
            f"Return ONLY the JSON array, no other text."
        )

        result = await self.ollama.generate(prompt, system="You create step-by-step plans using available tools. Return ONLY valid JSON arrays.")
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            result = "\n".join(lines)

        steps = json.loads(result)
        if isinstance(steps, list):
            return steps
        return self._default_steps(goal)

    def _default_steps(self, goal: str) -> list[dict]:
        return [{"description": goal, "tool": "", "parameters": {"input": goal}}]

    async def replan(self, plan: Plan, failed_step: PlanStep, reason: str) -> Plan:
        if self.ollama:
            try:
                remaining = [s for s in plan.steps if s.status == "pending"]
                context = f"Step {failed_step.step_id} ({failed_step.description}) failed: {reason}\nRemaining: {[s.description for s in remaining]}"
                new_steps = await self._llm_decompose(f"{plan.goal} -- Context: {context}")
                for s in new_steps:
                    plan.steps.append(
                        PlanStep(
                            step_id=len(plan.steps) + 1,
                            description=s.get("description", ""),
                            tool_name=s.get("tool", ""),
                            parameters=s.get("parameters", {}),
                        )
                    )
            except Exception as e:
                logger.warning("Replanning failed: %s", e)
        return plan
