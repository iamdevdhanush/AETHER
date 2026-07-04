"""
AETHER Reasoning Engine
Continuous think -> choose -> execute -> observe -> reflect loop.

Iteration limits by route:
  KNOWLEDGE:       1 iteration (handled before reaching this engine)
  DESKTOP_ACTION:  2-5 iterations
  MIXED_TASK:      5-15 iterations

Stops immediately once the goal is complete.
Never keeps looping.
"""

import logging
from typing import Optional, AsyncIterator

from core.models import ReasoningState, Plan, PlanStep
from core.tool_registry import ToolRegistry
from core.observation_engine import ObservationEngine
from core.reflection_engine import ReflectionEngine
from core.permission_manager import PermissionManager, RiskLevel
from models.tool_base import ToolObservation

logger = logging.getLogger(__name__)


class ReasoningEngine:

    def __init__(self, tool_registry: ToolRegistry,
                 observation_engine: ObservationEngine,
                 reflection_engine: ReflectionEngine,
                 permission_manager: PermissionManager,
                 ollama=None):
        self.tool_registry = tool_registry
        self.observation_engine = observation_engine
        self.reflection_engine = reflection_engine
        self.permission_manager = permission_manager
        self.ollama = ollama
        self._state = ReasoningState()

    async def think(self, context: str, plan: Optional[Plan] = None) -> ReasoningState:
        if plan and plan.current_step < len(plan.steps):
            step = plan.steps[plan.current_step]
            self._state = ReasoningState(
                thought=f"Executing step {step.step_id}: {step.description}",
                selected_tool=step.tool_name,
                parameters=step.parameters,
            )
            return self._state

        if self.ollama:
            try:
                return await self._llm_think(context)
            except Exception as e:
                logger.warning("LLM think failed: %s", e)

        self._state = ReasoningState(
            thought="No LLM available for reasoning.",
            is_complete=True,
        )
        return self._state

    async def _llm_think(self, context: str) -> ReasoningState:
        tools_desc = "\n".join(
            f"  - {t['name']}: {t['description']}"
            for t in self.tool_registry.list_tools()
        )

        prompt = (
            f"You are AETHER, an autonomous desktop AI agent.\n\n"
            f"Context: {context}\n\n"
            f"Available tools:\n{tools_desc}\n\n"
            f"CRITICAL RULE: Before choosing a tool, ask yourself:\n"
            f"\"Can I answer this from my existing knowledge without touching the OS?\"\n"
            f"If YES, set tool_name to empty and is_complete to true.\n\n"
            f"Decide what to do next. Respond with EXACTLY:\n"
            f"thought|tool_name|parameters_json|is_complete(true/false)\n\n"
            f"Examples:\n"
            "Open Chrome|browser|{\"input\":\"\"}|false\n"
            "I already know the answer||{}|true\n\n"
            f"Parameters must be valid JSON."
        )

        result = await self.ollama.generate(prompt, system="You are an autonomous agent. Choose tools and act. Never explain — just decide.")
        result = result.strip()
        parts = result.split("|", 3)
        if len(parts) == 4:
            thought = parts[0].strip()
            tool = parts[1].strip() or None
            try:
                params = __import__("json").loads(parts[2].strip())
            except Exception:
                params = {}
            is_complete = parts[3].strip().lower() == "true"
            return ReasoningState(
                thought=thought, selected_tool=tool,
                parameters=params, is_complete=is_complete,
            )

        return ReasoningState(thought="Could not parse reasoning.", is_complete=True)

    async def execute_step(self, tool_name: str, params: dict) -> ToolObservation:
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolObservation(
                stdout="", stderr=f"Tool '{tool_name}' not found",
                exit_code=-1, success=False,
            )

        risk = self.permission_manager.assess_risk(tool_name, params)
        if risk == RiskLevel.HIGH:
            ok = await self.permission_manager.request_approval(tool_name, params, "")
            if not ok:
                return ToolObservation(
                    stdout="", stderr=f"High-risk action denied: {tool_name}",
                    exit_code=-2, success=False,
                )

        return await tool.execute(params)

    async def run_loop(self, context: str, plan: Optional[Plan] = None,
                       on_step=None,
                       max_iterations: int = 5) -> AsyncIterator[ReasoningState]:
        """
        Main reasoning loop. Yields each state for UI consumption.

        Args:
          context: The task context string.
          plan: Optional step-by-step plan.
          on_step: Optional callback(state) for external listeners.
          max_iterations: Maximum loop iterations (default 5).
                          Knowledge=1, DesktopAction=2-5, MixedTask=5-15.
        """
        for iteration in range(max_iterations):
            state = await self.think(context, plan)
            self._state = state

            if on_step:
                await on_step(state)

            yield state

            if state.is_complete:
                logger.info("Reasoning loop: complete after %d iteration(s)", iteration + 1)
                break

            if not state.selected_tool:
                logger.info("Reasoning loop: no tool selected, ending after %d iter(s)", iteration + 1)
                break

            tool_result = await self.execute_step(
                state.selected_tool, state.parameters,
            )
            await self.observation_engine.observe(
                state.selected_tool, state.parameters, tool_result,
            )

            obs = self.observation_engine.get_last()
            state.observation = obs

            tool_data = {
                "success": tool_result.success,
                "exit_code": tool_result.exit_code,
                "stderr": tool_result.stderr,
                "stdout": tool_result.stdout,
            }
            reflection, action = await self.reflection_engine.reflect(
                state.selected_tool, tool_data,
                state.thought,
            )
            state.reflection = reflection

            if action == "continue":
                if plan:
                    plan.current_step += 1
            elif action == "retry":
                pass
            elif action == "skip":
                if plan:
                    plan.current_step += 1
            elif action == "blocked":
                state.is_complete = True
                yield state
                break

            context = (
                f"Previous step: {state.thought}\n"
                f"Tool: {state.selected_tool}\n"
                f"Result: {tool_result.summary()}\n"
                f"Reflection: {reflection}\n"
                f"Action: {action}\n"
                f"Continue..."
            )

            if on_step:
                await on_step(state)

        else:
            logger.info("Reasoning loop: reached max iterations (%d)", max_iterations)
