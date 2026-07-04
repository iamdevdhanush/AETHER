"""
AETHER Agent Runtime v2
Orchestrates the full autonomous agent pipeline:

User Request → Intent Engine → Planner (if complex) → Reasoning Loop:
  Think → Choose Tool → Execute → Observe → Reflect → Repeat

Only conversational responses go directly to the LLM.
Everything else becomes an action.
"""

import logging
import asyncio
from typing import Optional, AsyncIterator

from core.models import Intent, Plan, PlanStep, ReasoningState
from core.intent_engine import IntentEngine
from core.tool_registry import ToolRegistry
from core.planner import Planner
from core.reasoning_engine import ReasoningEngine
from core.observation_engine import ObservationEngine
from core.reflection_engine import ReflectionEngine
from core.permission_manager import PermissionManager
from models.tool_base import ToolObservation

logger = logging.getLogger(__name__)


class AgentRuntime:

    def __init__(self, tool_registry: ToolRegistry,
                 intent_engine: IntentEngine,
                 planner: Planner,
                 reasoning_engine: ReasoningEngine,
                 observation_engine: ObservationEngine,
                 reflection_engine: ReflectionEngine,
                 permission_manager: PermissionManager,
                 ollama=None, memory_service=None,
                 conversation_service=None, bridge=None):
        self.tool_registry = tool_registry
        self.intent_engine = intent_engine
        self.planner = planner
        self.reasoning_engine = reasoning_engine
        self.observation_engine = observation_engine
        self.reflection_engine = reflection_engine
        self.permission_manager = permission_manager
        self.ollama = ollama
        self.memory_service = memory_service
        self.conversation_service = conversation_service
        self.bridge = bridge

        self._current_plan: Optional[Plan] = None

    async def process(self, text: str) -> Optional[str]:
        """
        Process a user message through the full agent pipeline.

        Returns:
          str | None — A text response if the intent was handled.
                      Returns None for chat intents (streaming handled by bridge).
        """
        intent = await self.intent_engine.classify(text)
        self._emit("intent_detected", intent.explanation, {
            "type": intent.type,
            "tool": intent.tool_name,
            "confidence": intent.confidence,
        })

        logger.info("Intent: %s (tool=%s, conf=%.2f)", intent.type, intent.tool_name, intent.confidence)

        if intent.type == "knowledge":
            return await self._handle_knowledge(text, intent)

        if intent.type == "complex":
            return await self._handle_complex(text, intent)

        if intent.type == "tool":
            return await self._handle_tool(intent)

        return None

    async def _handle_tool(self, intent: Intent) -> str:
        tool = self.tool_registry.get(intent.tool_name) if intent.tool_name else None
        if not tool:
            fallback = await self._try_fallback(intent)
            if fallback:
                return fallback

            self._emit("error", f"Tool '{intent.tool_name}' not found")
            return f"Sorry, Sir. The '{intent.tool_name}' tool is not available."

        risk = self.permission_manager.assess_risk(intent.tool_name, intent.parameters)
        if risk.value == "high":
            self._emit("executing", f"Requires approval: {intent.tool_name}", {"risk": "high"})
            ok = await self.permission_manager.request_approval(
                intent.tool_name, intent.parameters, intent.explanation,
            )
            if not ok:
                self._emit("error", f"High-risk action denied: {intent.tool_name}")
                return f"Denied, Sir. {intent.explanation} requires confirmation."

        self._emit("tool_selected", intent.tool_name)
        self._emit("executing", f"Executing {intent.tool_name}...")

        obs = await tool.execute(intent.parameters)
        await self.observation_engine.observe(intent.tool_name, intent.parameters, obs)

        if obs.success:
            self._emit("result", obs.summary())
            response = self._format_tool_result(intent.tool_name, obs)
            if self.memory_service:
                await self.memory_service.store_workflow(
                    intent.explanation,
                    [{"tool": intent.tool_name, "params": intent.parameters}],
                    obs.summary(),
                )
            return response

        self._emit("error", obs.stderr[:200])
        reflection, action = await self.reflection_engine.reflect(
            intent.tool_name,
            {"success": obs.success, "exit_code": obs.exit_code, "stderr": obs.stderr, "stdout": obs.stdout},
            intent.explanation,
        )
        logger.info("Reflection: %s → %s", reflection, action)

        if action in ("retry", "retry_alt"):
            self._emit("executing", f"Retrying {intent.tool_name}...")
            obs2 = await tool.execute(intent.parameters)
            await self.observation_engine.observe(intent.tool_name + "_retry", intent.parameters, obs2)
            if obs2.success:
                self._emit("result", obs2.summary())
                return self._format_tool_result(intent.tool_name, obs2)
            return f"Failed after retry: {obs2.stderr[:200]}"

        return f"Failed: {obs.stderr[:300]}"

    async def _handle_knowledge(self, text: str, intent: Intent) -> str:
        if not self.ollama:
            return "I don't have an LLM available to answer that, Sir."

        self._emit("executing", "Thinking...", {"mode": "knowledge"})
        try:
            system = (
                "You are AETHER, an autonomous desktop AI agent. "
                "Answer the user's question concisely and accurately. "
                "Use markdown formatting when helpful. "
                "If the user asks about performing an action, use your tools — "
                "do not just explain how to do it."
            )
            if self.memory_service:
                memories = await self.memory_service.get_relevant_memories(text)
                if memories:
                    memory_text = "\n".join(f"- {m['content']}" for m in memories[:5])
                    system += f"\n\nRelevant context from memory:\n{memory_text}"

            result = await self.ollama.generate(text, system=system)
            self._emit("result", result[:200])
            return result
        except Exception as e:
            logger.error("Knowledge Q&A failed: %s", e)
            return f"Failed to answer: {e}"

    async def _handle_complex(self, text: str, intent: Intent) -> str:
        self._emit("planning", f"Creating plan for: {text[:80]}")

        plan = await self.planner.create_plan(text)
        self._current_plan = plan

        if not plan.steps:
            return "I couldn't break that down into steps, Sir."

        if self.memory_service:
            self.memory_service.set_task(
                text,
                [s.description for s in plan.steps],
            )

        plan.status = "running"
        steps_desc = " → ".join(s.description for s in plan.steps)
        self._emit("plan_created", f"Plan: {steps_desc}",
                     {"steps": [s.__dict__ for s in plan.steps]})

        results = []
        async for state in self.reasoning_engine.run_loop(
            context=f"Task: {text}\nPlan: {steps_desc}",
            plan=plan,
        ):
            if state.selected_tool:
                obs = state.observation or {}
                success = obs.get("success", False) if isinstance(obs, dict) else True
                step_result = "✓" if success else "✗"
                results.append(f"{step_result} {state.thought}")

        plan.status = "completed"
        self._emit("plan_complete", f"Completed {len(results)} steps")

        if self.memory_service:
            await self.memory_service.store_workflow(
                text,
                [{"tool": s.tool_name, "params": s.parameters} for s in plan.steps],
                "\n".join(results),
            )
            self.memory_service.clear_working()

        summary = "\n".join(f"  {r}" for r in results)
        return f"Completed, Sir.\n{summary}"

    async def _try_fallback(self, intent: Intent) -> Optional[str]:
        if not intent.tool_name or not self.ollama:
            return None
        tool_obj = self.tool_registry.get(intent.tool_name)
        if tool_obj:
            return None
        tools_desc = "\n".join(t.name() for t in self.tool_registry._tools.values())
        prompt = (
            f"The tool '{intent.tool_name}' was requested but is not available.\n"
            f"Available tools: {tools_desc}\n\n"
            f"Can any available tool fulfill the request: {intent.explanation}?\n"
            f"Respond: tool_name or 'none'"
        )
        try:
            result = await self.ollama.generate(prompt, system="You map requests to available tools.")
            result = result.strip().lower()
            if result in self.tool_registry.list_tools():
                return None
        except:
            pass
        return None

    def _format_tool_result(self, tool_name: str, obs: ToolObservation) -> str:
        if obs.success:
            summary = obs.summary()
            if len(summary) > 500:
                summary = summary[:497] + "..."
            return f"{summary}"
        return f"Failed: {obs.stderr[:300]}"

    def _emit(self, event_type: str, description: str, metadata: dict = None):
        if self.bridge:
            import time
            ev = {
                "type": event_type,
                "description": description,
                "timestamp": int(time.time() * 1000),
            }
            if metadata:
                ev["metadata"] = metadata
            self.bridge.timelineEventAdded.emit(ev)
