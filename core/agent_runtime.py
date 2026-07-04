"""
AETHER Agent Runtime
Orchestrates the full execution pipeline:
  Intent → Selected Tool → Executing → Result
Routes user messages to tools, knowledge Q&A, or conversational AI.
"""

import logging
from typing import Optional

from core.intent_engine import IntentEngine, Intent

logger = logging.getLogger(__name__)


class AgentRuntime:

    def __init__(self, ollama, plugin_manager, conversation_service,
                 memory_service, bridge):
        self.ollama = ollama
        self.plugin_manager = plugin_manager
        self.conversation_service = conversation_service
        self.memory_service = memory_service
        self.bridge = bridge
        self.intent_engine = IntentEngine(ollama)

    async def process(self, text: str) -> Optional[str]:
        """
        Process a user message through the agent pipeline.

        Returns:
            str | None - A result string if the intent was handled
                          by a tool or direct Q&A. Returns None for
                          chat intents, signalling the bridge to use
                          streaming conversation.
        """
        intent = await self.intent_engine.classify(text)
        self.bridge._emit_timeline_event(
            "intent_detected",
            intent.explanation,
        )

        if intent.type == "tool":
            return await self._handle_tool(text, intent)

        if intent.type == "question":
            return await self._handle_question(text, intent)

        return None  # signal chat streaming

    async def _handle_tool(self, text: str, intent: Intent) -> str:
        plugin = self.plugin_manager.get_plugin(intent.plugin)
        if not plugin:
            msg = f"No registered tool available for '{intent.plugin}'"
            self.bridge._emit_timeline_event("error", msg)
            return msg

        self.bridge._emit_timeline_event("tool_selected", intent.plugin)

        args = intent.args or {}
        if not args.get("input"):
            args = await self._extract_tool_args(text, intent.plugin)

        self.bridge._emit_timeline_event(
            "executing",
            f"Running {intent.plugin}...",
        )

        try:
            result = await plugin.execute(args)
            summary = (result[:300] + "...") if len(result) > 300 else result
            self.bridge._emit_timeline_event("result", summary)
            return result
        except Exception as e:
            logger.exception("Tool execution failed: %s", intent.plugin)
            err = f"Error executing {intent.plugin}: {e}"
            self.bridge._emit_timeline_event("error", err)
            return err

    async def _extract_tool_args(self, text: str, plugin_name: str) -> dict:
        if not self.ollama:
            return {"input": text}

        try:
            return await self.ollama.extract_arguments(text, plugin_name)
        except Exception as e:
            logger.warning(
                "Argument extraction failed for %s: %s", plugin_name, e,
            )
            return {"input": text}

    async def _handle_question(self, text: str, intent: Intent) -> str:
        self.bridge._emit_timeline_event(
            "executing",
            "Consulting knowledge...",
        )
        try:
            result = await self.ollama.generate(
                text,
                system=(
                    "You are AETHER, a helpful desktop AI assistant. "
                    "Answer the user's question concisely and accurately. "
                    "Use markdown formatting when helpful."
                ),
            )
            summary = (result[:300] + "...") if len(result) > 300 else result
            self.bridge._emit_timeline_event("result", summary)
            return result
        except Exception as e:
            logger.error("Knowledge Q&A failed: %s", e)
            err = f"Failed to answer question: {e}"
            self.bridge._emit_timeline_event("error", err)
            return err
