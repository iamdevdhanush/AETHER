"""
AETHER Agent Runtime v3
Orchestrates the autonomous agent pipeline with strict intent routing:

User Request
  |
  v
Intent Router (4 routes)
  |
  +-- KNOWLEDGE      -> LLM only. No planner. No tools.
  +-- DESKTOP_ACTION -> Planner -> Tool Selection -> Execution (2-5 iterations)
  +-- MIXED_TASK     -> Planner + LLM + Tools (5-15 iterations)
  +-- UNKNOWN        -> Ask one clarifying question.

Planner Rules:
  - Only creates plans if tools are required.
  - NEVER plans for conversation, writing, translation, summarization, explanation.

Tool Gate:
  - Before any tool call: "Can LLM answer without touching the OS?"
  - If YES -> do NOT use tools.
  - If NO  -> use the minimum number of tools.
"""

import logging
import asyncio
from typing import Optional, AsyncIterator

from core.models import Intent, Plan, PlanStep, ReasoningState
from core.intent_router import IntentRouter, Route, IntentRouteResult
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
                 intent_router: IntentRouter,
                 planner: Planner,
                 reasoning_engine: ReasoningEngine,
                 observation_engine: ObservationEngine,
                 reflection_engine: ReflectionEngine,
                 permission_manager: PermissionManager,
                 ollama=None, memory_service=None,
                 conversation_service=None, bridge=None):
        self.tool_registry = tool_registry
        self.intent_router = intent_router
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
        route_result = await self.intent_router.classify(text)
        self._emit("intent_detected",
            f"Route: {route_result.route.value.upper()} — {route_result.explanation}",
            {"route": route_result.route.value,
             "confidence": route_result.confidence,
             "tool": route_result.suggested_tool or "",
             "explanation": route_result.explanation})

        logger.info("INTENT ROUTE: %s (conf=%.2f, tool=%s, explanation=%s)",
                     route_result.route.value, route_result.confidence,
                     route_result.suggested_tool, route_result.explanation)

        if route_result.route == Route.KNOWLEDGE:
            return await self._handle_knowledge(text, route_result)

        if route_result.route == Route.DESKTOP_ACTION:
            return await self._handle_desktop_action(text, route_result)

        if route_result.route == Route.MIXED_TASK:
            return await self._handle_mixed_task(text, route_result)

        return await self._handle_unknown(text)

    # ── Route: KNOWLEDGE ─────────────────────────────────────────────────

    async def _handle_knowledge(self, text: str, route: IntentRouteResult) -> str:
        if not self.ollama:
            return "I don't have an LLM available to answer that, Sir."

        self._emit("executing", "Responding with LLM (no tools needed)",
                     {"mode": "knowledge", "route": "knowledge"})
        try:
            system = (
                "You are AETHER, an autonomous desktop AI agent. "
                "Answer the user's question concisely and accurately. "
                "Use markdown formatting when helpful. "
                "This is a PURE KNOWLEDGE request. Do NOT use any tools. "
                "Do NOT suggest running commands. Just answer with your knowledge."
            )
            if self.memory_service:
                memories = await self.memory_service.get_relevant_memories(text)
                if memories:
                    memory_text = "\n".join(f"- {m['content']}" for m in memories[:5])
                    system += f"\n\nRelevant context from memory:\n{memory_text}"

            result = await self.ollama.generate(text, system=system)
            self._emit("result", f"LLM response ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error("Knowledge handler failed: %s", e)
            return f"Failed to answer: {e}"

    # ── Route: DESKTOP_ACTION ────────────────────────────────────────────

    async def _handle_desktop_action(self, text: str, route: IntentRouteResult) -> str:
        self._emit("planning", f"Creating plan for desktop action: {text[:80]}",
                     {"route": "desktop_action"})

        plan = await self.planner.create_plan(text, strict=True)
        self._current_plan = plan

        if not plan.steps:
            if self.ollama:
                self._emit("executing", "Falling back to LLM — no actionable steps",
                             {"route": "desktop_action"})
                return await self.ollama.generate(text,
                    system="The request requires no tools. Answer directly.")
            return "I couldn't determine what action to take, Sir."

        plan.status = "running"
        steps_desc = " → ".join(s.description for s in plan.steps)
        self._emit("plan_created", f"Desktop action plan: {steps_desc}",
                     {"steps": [s.__dict__ for s in plan.steps], "route": "desktop_action"})

        if self.memory_service:
            self.memory_service.set_task(text, [s.description for s in plan.steps])

        results = []
        async for state in self.reasoning_engine.run_loop(
            context=f"Desktop action: {text}\nPlan: {steps_desc}",
            plan=plan,
            max_iterations=5,
        ):
            if state.selected_tool:
                obs = state.observation or {}
                success = obs.get("success", False) if isinstance(obs, dict) else True
                step_result = "✓" if success else "✗"
                results.append(f"{step_result} {state.thought}")
            if state.is_complete:
                break

        plan.status = "completed"
        self._emit("plan_complete",
            f"Completed {len(results)} step(s)",
            {"route": "desktop_action"})

        if self.memory_service:
            await self.memory_service.store_workflow(
                text,
                [{"tool": s.tool_name, "params": s.parameters} for s in plan.steps],
                "\n".join(results),
            )
            self.memory_service.clear_working()

        if not results:
            return "Done, Sir."

        summary = "\n".join(f"  {r}" for r in results)
        return f"Done, Sir.\n{summary}"

    # ── Route: MIXED_TASK ────────────────────────────────────────────────

    async def _handle_mixed_task(self, text: str, route: IntentRouteResult) -> str:
        self._emit("planning", f"Creating plan for multi-step task: {text[:80]}",
                     {"route": "mixed_task"})

        plan = await self.planner.create_plan(text, strict=False)
        self._current_plan = plan

        if not plan.steps:
            if self.ollama:
                self._emit("executing", "Falling back to LLM — no actionable steps",
                             {"route": "mixed_task"})
                return await self._handle_knowledge(text, route)
            return "I couldn't break that down, Sir."

        plan.status = "running"
        steps_desc = " → ".join(s.description for s in plan.steps)
        self._emit("plan_created", f"Mixed task plan: {steps_desc}",
                     {"steps": [s.__dict__ for s in plan.steps], "route": "mixed_task"})

        if self.memory_service:
            self.memory_service.set_task(text, [s.description for s in plan.steps])

        results = []
        async for state in self.reasoning_engine.run_loop(
            context=f"Task: {text}\nPlan: {steps_desc}",
            plan=plan,
            max_iterations=15,
        ):
            if state.selected_tool:
                obs = state.observation or {}
                success = obs.get("success", False) if isinstance(obs, dict) else True
                step_result = "✓" if success else "✗"
                results.append(f"{step_result} {state.thought}")
            elif state.thought and not state.selected_tool:
                results.append(f"  {state.thought}")
            if state.is_complete:
                break

        plan.status = "completed"
        self._emit("plan_complete",
            f"Completed {len(results)} step(s)",
            {"route": "mixed_task"})

        if self.memory_service:
            await self.memory_service.store_workflow(
                text,
                [{"tool": s.tool_name, "params": s.parameters} for s in plan.steps],
                "\n".join(results),
            )
            self.memory_service.clear_working()

        if not results:
            return "Done, Sir."

        summary = "\n".join(f"  {r}" for r in results)
        return f"Completed, Sir.\n{summary}"

    # ── Route: UNKNOWN ───────────────────────────────────────────────────

    async def _handle_unknown(self, text: str) -> str:
        self._emit("executing",
            "Request unclear — asking for clarification",
            {"route": "unknown"})
        return (
            "I'm not sure what you'd like me to do, Sir.\n\n"
            "Here's what I can help with:\n\n"
            "**Knowledge** — Ask me anything (explain, summarize, translate, write code)\n"
            "**Desktop Actions** — Open apps, run commands, manage files, system control\n"
            "**Mixed Tasks** — Multi-step tasks combining analysis and actions\n\n"
            "For example:\n"
            "  • \"What is Python?\"\n"
            "  • \"Open Chrome\"\n"
            "  • \"Summarize this file then save it\"\n"
            "  • \"Create a folder called projects\""
        )

    # ── Tool Gate ────────────────────────────────────────────────────────

    async def _tool_gate(self, tool_name: str, params: dict, context: str) -> bool:
        """
        Before calling a tool, check: can the LLM answer without touching the OS?
        If YES -> do NOT use tools. Return False.
        If NO  -> use the tool. Return True.
        """
        if not self.ollama:
            return True

        try:
            prompt = (
                f"Can you answer this request using ONLY your existing knowledge, "
                f"WITHOUT running any commands or using any tools?\n\n"
                f"Request: {context}\n"
                f"Proposed tool: {tool_name}\n"
                f"Proposed parameters: {params}\n\n"
                f"Reply EXACTLY: YES or NO"
            )
            result = await self.ollama.generate(prompt,
                system="You decide whether a tool is needed. Be strict.")
            answer = result.strip().upper()
            if answer.startswith("NO"):
                return True
            return False
        except Exception as e:
            logger.warning("Tool gate check failed (defaulting to allow): %s", e)
            return True

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
