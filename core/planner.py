"""
AETHER Planner
Decomposes complex requests into structured, actionable steps.

PLANNER RULES:
  - Only create execution plans if tools are required.
  - Never create plans for pure conversation.
  - Never create plans for writing code.
  - Never create plans for translation.
  - Never create plans for summarization.
  - Never create plans for explanations.

If the goal is pure knowledge, the planner returns an empty plan
and the caller falls back to the LLM directly.
"""

import logging
import json
import re
from typing import Optional

from core.models import Plan, PlanStep
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# These patterns trigger strict rejection — the planner REFUSES to create
# tool-based plans for any of these.
KNOWLEDGE_ONLY_PATTERNS = re.compile(
    r"^(explain|describe|define|clarify|elaborate|summarize|summarise|translate|"
    r"interpret|convert|tell me about|tell me what|write\s+(a|an|the)\s+(python|"
    r"script|function|program|code|class)|generate\s+(a|an|the)\s+(python|script|"
    r"function|code)|what\s+is|what\s+are|how\s+(to|does|do|can|is|are|would)|"
    r"why\s+(does|do|did|is|are|would)|compare|contrast|differentiate|list|name)",
    re.I,
)


class Planner:

    def __init__(self, tool_registry: ToolRegistry, ollama=None):
        self.tool_registry = tool_registry
        self.ollama = ollama

    async def create_plan(self, goal: str, strict: bool = True) -> Plan:
        """
        Create a plan for the given goal.

        Args:
          goal: The user's request
          strict: If True, refuse to create plans for knowledge-only requests.
                  When False (mixed tasks), some knowledge steps may be included.

        Returns:
          Plan with steps if actionable, or empty Plan if knowledge-only.
        """
        plan = Plan(goal=goal)

        if strict and self._is_knowledge_only(goal):
            logger.info("Planner skipped — knowledge-only request: %s", goal[:80])
            self._emit_skip(goal, "knowledge-only request")
            return plan

        if self.ollama:
            try:
                steps = await self._llm_decompose(goal, strict)
            except Exception as e:
                logger.warning("LLM planning failed: %s", e)
                return plan
        else:
            return plan

        if not steps:
            return plan

        for i, step_data in enumerate(steps):
            tname = step_data.get("tool", "")
            if tname:
                plan.steps.append(
                    PlanStep(
                        step_id=i + 1,
                        description=step_data.get("description", ""),
                        tool_name=tname,
                        parameters=step_data.get("parameters", {"input": goal}),
                    )
                )

        if not plan.steps:
            logger.info("Planner returned no actionable steps for: %s", goal[:80])

        logger.info("Created plan with %d step(s) for: %s",
                     len(plan.steps), goal[:80])
        return plan

    def _is_knowledge_only(self, goal: str) -> bool:
        """Check if the goal is a pure knowledge request that needs no tools."""
        goal_lower = goal.lower().strip()
        if KNOWLEDGE_ONLY_PATTERNS.match(goal_lower):
            return True
        if goal_lower.endswith("?") and len(goal_lower) < 200:
            return True
        return False

    def _emit_skip(self, goal: str, reason: str):
        logger.info("Planner: Skipped — %s. Goal: %s", reason, goal[:80])

    async def _llm_decompose(self, goal: str, strict: bool) -> list[dict]:
        tools_desc = "\n".join(
            f"  - {t['name']}: {t['description']}"
            for t in self.tool_registry.list_tools()
        )

        strict_rule = (
            "RULES:\n"
            "- If the goal is a PURE KNOWLEDGE request (explain, translate, summarize,\n"
            "  write code, definition, question), return an empty JSON array [].\n"
            "- Do NOT create tool steps for writing code, translation, or summarization.\n"
            "- Only create steps that involve ACTUAL tool use on the operating system.\n"
        ) if strict else (
            "RULES:\n"
            "- Create steps that involve ACTUAL tool use on the operating system.\n"
            "- For mixed tasks (read+save, analyze+write), create the appropriate tool steps.\n"
            "- Skip steps that are pure knowledge without a tool component.\n"
        )

        prompt = (
            f"Break this request into sequential steps using available tools.\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            f"Request: \"{goal}\"\n\n"
            f"{strict_rule}\n"
            f"Return a JSON array of steps. Each step: {{\n"
            f'  "description": "what to do",\n'
            f'  "tool": "tool_name",\n'
            f'  "parameters": {{"input": "..."}}\n'
            f"}}\n\n"
            f"If no tools are needed, return an empty JSON array [].\n\n"
            f"Example valid response:\n"
            f'[{{"description": "Open VS Code", "tool": "vscode", "parameters": {{"input": ""}}}}]\n\n'
            f"Return ONLY the JSON array, no other text."
        )

        result = await self.ollama.generate(prompt,
            system="You create step-by-step plans using available tools. "
                   "Return ONLY valid JSON arrays. Return [] if no tools are needed.")
        result = result.strip()

        if result.startswith("```"):
            lines = result.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            result = "\n".join(lines)

        try:
            steps = json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Planner LLM returned invalid JSON: %s", result[:100])
            return []

        if isinstance(steps, list):
            return steps
        return []

    async def replan(self, plan: Plan, failed_step: PlanStep, reason: str) -> Plan:
        if self.ollama:
            try:
                remaining = [s for s in plan.steps if s.status == "pending"]
                context = (
                    f"Step {failed_step.step_id} ({failed_step.description}) "
                    f"failed: {reason}\n"
                    f"Remaining: {[s.description for s in remaining]}"
                )
                new_steps = await self._llm_decompose(
                    f"{plan.goal} -- Context: {context}",
                    strict=False,
                )
                for s in new_steps:
                    tname = s.get("tool", "")
                    if tname:
                        plan.steps.append(
                            PlanStep(
                                step_id=len(plan.steps) + 1,
                                description=s.get("description", ""),
                                tool_name=tname,
                                parameters=s.get("parameters", {"input": plan.goal}),
                            )
                        )
            except Exception as e:
                logger.warning("Replanning failed: %s", e)
        return plan
