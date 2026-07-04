"""
AETHER Intent Engine v2
Classifies every user request into one of:
  - tool:    Direct tool execution (single action)
  - knowledge: Factual question for the LLM
  - chat:    General conversation / greeting
  - complex: Multi-step operation that requires planning

Classification is strict: knowledge questions go to LLM,
everything actionable goes to a tool or the planner.
"""

import logging
import re
from typing import Optional

from core.models import Intent
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

TOOL_TRIGGERS: dict[str, list[str]] = {
    "browser":     ["open", "go to", "navigate", "search for", "browse", "website", "url", "google", "youtube"],
    "vscode":      ["vs code", "visual studio code", "vscode", "open in code", "launch code", "code editor"],
    "terminal":    ["run", "execute", "command", "terminal", "shell", "run command"],
    "filesystem":  ["create folder", "create directory", "list files", "read file", "delete file", "write file",
                    "save file", "mkdir", "show directory", "list directory", "browse folder"],
    "executor":    ["run python", "execute code", "run code", "python script"],
    "sysmon":      ["system status", "system info", "cpu", "memory", "ram", "disk", "battery", "network",
                    "process", "stats", "performance"],
    "docker":      ["docker", "container", "image", "docker ps", "docker run", "docker stop", "docker start", "docker pull"],
    "git":         ["git", "git status", "git pull", "git push", "git commit", "git add", "git log", "git clone"],
    "system":      ["shutdown", "restart", "reboot", "sleep", "hibernate", "lock computer", "screenshot"],
    "clipboard":   ["copy", "paste", "clipboard"],
    "window":      ["window", "minimize", "maximize", "focus", "switch window", "snap"],
    "notification":["notify", "notification", "alert"],
}

QUESTION_PREFIXES = re.compile(
    r"^(what|why|when|where|who|how|is|are|was|were|do|does|did|can|could|would|should|will|shall|has|have|had|tell|explain|define|describe|show)\b",
    re.I,
)


class IntentEngine:

    def __init__(self, tool_registry: ToolRegistry, ollama=None):
        self.tool_registry = tool_registry
        self.ollama = ollama

    async def classify(self, text: str) -> Intent:
        text = text.strip()
        if not text:
            return Intent(type="chat", confidence=1.0, explanation="Empty input")

        intent = self._fast_path(text)
        if intent.confidence >= 0.7:
            logger.info("Fast path: %s (tool=%s, conf=%.2f)", intent.type, intent.tool_name, intent.confidence)
            return intent

        if self.ollama:
            try:
                llm_intent = await self._llm_classify(text)
                if llm_intent and llm_intent.confidence > intent.confidence:
                    logger.info("LLM path: %s (tool=%s, conf=%.2f)", llm_intent.type, llm_intent.tool_name, llm_intent.confidence)
                    return llm_intent
            except Exception as e:
                logger.warning("LLM intent classification failed: %s", e)

        return intent

    def _fast_path(self, text: str) -> Intent:
        text_lower = text.lower().strip()
        best_tool = None
        best_score = 0.0
        best_param = {}

        for tool_name, triggers in TOOL_TRIGGERS.items():
            for trigger in triggers:
                if trigger in text_lower:
                    score = len(trigger) / max(len(text_lower), 1)
                    if text_lower.startswith(trigger):
                        score += 0.25
                    if score > best_score:
                        best_score = score
                        best_tool = tool_name
                        best_param = self._extract_params(text, tool_name)

        if best_tool and best_score >= 0.35:
            return Intent(
                type="tool",
                tool_name=best_tool,
                parameters=best_param or {"input": text},
                confidence=min(best_score + 0.2, 1.0),
                explanation=f"Execute {best_tool}",
            )

        if text_lower.endswith("?") or QUESTION_PREFIXES.match(text_lower):
            return Intent(
                type="knowledge",
                confidence=0.7,
                explanation="Knowledge question",
            )

        multi_actions = self._detect_multiple_actions(text_lower)
        if multi_actions:
            return Intent(
                type="complex",
                confidence=0.8,
                explanation=f"Multi-step: {', '.join(multi_actions)}",
                requires_planning=True,
            )

        return Intent(type="chat", confidence=0.3, explanation="General conversation")

    def _extract_params(self, text: str, tool_name: str) -> dict:
        if tool_name == "browser":
            m = re.search(r"(?:open|go\s+to|navigate\s+to|launch)\s+(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": m.group(1)}
            m = re.search(r"search\s+(?:for\s+)?(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": m.group(1), "action": "search"}
        elif tool_name == "vscode":
            m = re.search(r"(?:open|launch|start)\s+(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": m.group(1)}
        elif tool_name == "terminal":
            m = re.search(r"(?:run|execute)\s+(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": m.group(1)}
        elif tool_name == "filesystem":
            m = re.search(r"(?:create|make)\s+(?:folder|directory)\s+(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": f"mkdir {m.group(1)}"}
            m = re.search(r"(?:read|open|show)\s+(?:file\s+)?(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": f"read {m.group(1)}"}
            m = re.search(r"(?:list|show)\s+(?:files|dir|directory|folder)\s+(.+?)(?:\s*)$", text, re.I)
            if m:
                return {"input": f"list {m.group(1)}"}
        return {"input": text}

    def _detect_multiple_actions(self, text_lower: str) -> list[str]:
        separators = [", then ", "; ", " and then ", ". next, ", ". after that, "]
        for sep in separators:
            if sep in text_lower:
                parts = text_lower.split(sep)
                actions = []
                for p in parts:
                    for tool_name, triggers in TOOL_TRIGGERS.items():
                        for trigger in triggers:
                            if trigger in p:
                                actions.append(tool_name)
                                break
                        if actions and actions[-1]:
                            break
                if len(actions) >= 2:
                    return actions
        return []

    async def _llm_classify(self, text: str) -> Optional[Intent]:
        if not self.ollama:
            return None

        tool_list = "\n".join(
            f"  - {name}: {desc}" for name, desc in TOOL_TRIGGERS.items()
        )

        prompt = (
            f"Classify this user request. Categories:\n"
            f"  tool: A single tool can handle it. Specify which tool.\n"
            f"  knowledge: The user is asking for information or explanation.\n"
            f"  complex: Multiple steps are needed (e.g. deploy, setup, configure).\n"
            f"  chat: Greeting, small talk, or unclear.\n\n"
            f"Available tools:\n{tool_list}\n\n"
            f"Request: \"{text}\"\n\n"
            f"Respond EXACTLY one line:\ncategory|tool_name_if_tool|brief_explanation"
        )

        result = await self.ollama.generate(prompt, system="You classify user intent precisely. Respond in exact format requested.")
        result = result.strip()
        parts = result.split("|", 2)
        if len(parts) >= 2:
            category = parts[0].strip().lower()
            tname = parts[1].strip() if len(parts) > 1 else ""
            expl = parts[2].strip() if len(parts) > 2 else ""
            if category == "tool" and tname:
                return Intent(type="tool", tool_name=tname, confidence=0.85, explanation=expl or f"Execute {tname}")
            if category == "knowledge":
                return Intent(type="knowledge", confidence=0.85, explanation=expl or "Knowledge question")
            if category == "complex":
                return Intent(type="complex", confidence=0.8, explanation=expl or "Multi-step operation", requires_planning=True)
        return Intent(type="chat", confidence=0.5, explanation="LLM defaulted to chat")
