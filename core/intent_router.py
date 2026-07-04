"""
AETHER Intent Router
Classifies every user request into one of four routes:

  KNOWLEDGE:       LLM only. No planner. No tools.
  DESKTOP_ACTION:  Planner -> Tool Selection -> Execution
  MIXED_TASK:      Planner + LLM + Tools
  UNKNOWN:         Ask one clarification question.

Enforces strict planner and tool-gating rules.
"""

import logging
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class Route(Enum):
    KNOWLEDGE = "knowledge"
    DESKTOP_ACTION = "desktop_action"
    MIXED_TASK = "mixed_task"
    UNKNOWN = "unknown"


@dataclass
class IntentRouteResult:
    route: Route
    original_text: str
    explanation: str
    confidence: float
    requires_planning: bool = False
    requires_tools: bool = False
    suggested_tool: Optional[str] = None
    suggested_parameters: dict = field(default_factory=dict)


KNOWLEDGE_PATTERNS = [
    r"^(what|who|where|when|why|how)\s+(is|are|was|were|does|do|did|can|could|would|will|shall|has|have|had)",
    r"^(explain|describe|define|clarify|elaborate)\s",
    r"^tell me (about|what|how|why|who|when|where)",
    r"^what is|^what are|^what was|^what were|^what does|^what do",
    r"^who is|^who are|^who was",
    r"^where is|^where are",
    r"^when (was|were|did|is|are)",
    r"^how (does|do|can|to|is|are|would|could|should)",
    r"^why (does|do|did|is|are|was|were|would)",
    r"^(summarize|summarise)\s",
    r"^(translate|interpret)\s",
    r"^(write|create|make|generate)\s+(a|an|the|some|me\s+a)\s+(python|script|function|program|code|class|app|file)",
    r"^write code (to|for|that)",
    r"^generate (a|an|the|some)\s+(python|script|function|code)",
    r"^(convert|transform)\s+(this|the|a|from)",
    r"^what('s| is) the (difference|similarity|relationship) between",
    r"^(compare|contrast|differentiate)\s",
    r"^(list|name|mention|give me)\s+(the|some|a few|examples|types|kinds)",
    r"^(is|are|was|were|does|do|did|can|has|have|had)\s+\w+(\s+\w+){0,5}\?$",
]

DESKTOP_ACTION_PATTERNS: dict[str, list[str]] = {
    "browser": [
        r"^(open|go to|navigate|launch)\s+(chrome|firefox|edge|browser|website|url|http)",
        r"^(search|google|youtube)\s",
    ],
    "vscode": [
        r"^(open|launch|start)\s+(vs\.?\s?code|visual studio|code editor|editor)",
        r"open in (vs\.?\s?code|code)",
    ],
    "terminal": [
        r"^(run|execute)\s+(command|script|program|this|that|the)",
    ],
    "filesystem": [
        r"^(create|make)\s+(folder|directory|file)",
        r"^(delete|remove|erase)\s+(folder|directory|file)",
        r"^(list|show)\s+(files|directory|folder|contents)",
        r"^read (file|the file|a file)",
    ],
    "system": [
        r"^(shutdown|restart|reboot|sleep|hibernate|lock)\s+(computer|pc|laptop|system|now)",
        r"^take (a )?screenshot",
        r"^screenshot",
    ],
    "docker": [
        r"^docker\s",
    ],
    "git": [
        r"^git\s",
    ],
}

MIXED_TASK_PATTERNS = [
    r".*\b(then|after that|next)\b.*",
    r".*\band\b.*\b(then|after|save|write|create)\b.*",
    r"(summarize|analyze|audit|scan|examine|investigate)\s+(this|the|a|that)\s+(folder|directory|project|codebase|repo)",
    r"(search|find|look up)\s+.*\b(then|and|after)\b",
    r"(summarize|analyze|explain|read)\s+.*\b(and|then|after)\b.*\b(save|write|create|send|open)\b",
    r"^(summarize|analyze)\s+.*\b(save|write|create|output|export)\b",
]


class IntentRouter:

    def __init__(self, tool_registry: ToolRegistry, ollama=None):
        self.tool_registry = tool_registry
        self.ollama = ollama

    async def classify(self, text: str) -> IntentRouteResult:
        text = text.strip()
        if not text:
            return IntentRouteResult(
                route=Route.UNKNOWN, original_text=text,
                explanation="Empty input", confidence=1.0,
            )

        result = self._check_knowledge(text)
        if result:
            return result

        result = self._check_desktop_action(text)
        if result and result.confidence >= 0.55:
            return result

        result = self._check_mixed_task(text)
        if result and result.confidence >= 0.55:
            return result

        if self.ollama:
            try:
                llm_result = await self._llm_classify(text)
                if llm_result:
                    return llm_result
            except Exception as e:
                logger.warning("LLM classification failed: %s", e)

        return IntentRouteResult(
            route=Route.UNKNOWN, original_text=text,
            explanation="Could not determine intent",
            confidence=0.0,
        )

    def _check_knowledge(self, text: str) -> Optional[IntentRouteResult]:
        tl = text.lower().strip()
        for pattern in KNOWLEDGE_PATTERNS:
            if re.match(pattern, tl):
                return IntentRouteResult(
                    route=Route.KNOWLEDGE, original_text=text,
                    explanation=f"Knowledge request — matched pattern",
                    confidence=0.85, requires_planning=False, requires_tools=False,
                )
        if tl.endswith("?") and len(tl) < 200:
            return IntentRouteResult(
                route=Route.KNOWLEDGE, original_text=text,
                explanation="Question detected — routing to LLM",
                confidence=0.6, requires_planning=False, requires_tools=False,
            )
        return None

    def _check_desktop_action(self, text: str) -> Optional[IntentRouteResult]:
        tl = text.lower().strip()
        best_tool = None
        best_score = 0.0
        for tool_name, patterns in DESKTOP_ACTION_PATTERNS.items():
            for pattern in patterns:
                m = re.match(pattern, tl)
                if m:
                    span_len = len(m.group(0))
                    score = 0.55 + (span_len / max(len(tl), 1)) * 0.35
                    if score > best_score:
                        best_score = score
                        best_tool = tool_name
        if best_tool and best_score >= 0.55:
            return IntentRouteResult(
                route=Route.DESKTOP_ACTION, original_text=text,
                explanation=f"Desktop action — requires {best_tool}",
                confidence=min(best_score, 1.0),
                requires_planning=True, requires_tools=True,
                suggested_tool=best_tool,
                suggested_parameters={"input": text},
            )
        return None

    def _check_mixed_task(self, text: str) -> Optional[IntentRouteResult]:
        tl = text.lower().strip()
        for pattern in MIXED_TASK_PATTERNS:
            if re.match(pattern, tl):
                return IntentRouteResult(
                    route=Route.MIXED_TASK, original_text=text,
                    explanation="Multi-step — requires planning + tools",
                    confidence=0.7,
                    requires_planning=True, requires_tools=True,
                )
        return None

    async def _llm_classify(self, text: str) -> Optional[IntentRouteResult]:
        tools_desc = "\n".join(
            f"  - {t['name']}: {t['description']}"
            for t in self.tool_registry.list_tools()
        )
        sys = (
            "You classify user requests into exactly one route.\n\n"
            "ROUTE KNOWLEDGE — information, explanation, translation, summarization, "
            "code writing (not execution), definitions, conceptual Q&A.\n"
            "  LLM only. No tools.\n\n"
            "ROUTE DESKTOP_ACTION — open app, run command, create/delete file, system control, docker, git.\n"
            "  Requires a specific tool.\n\n"
            "ROUTE MIXED_TASK — multiple steps combining actions AND knowledge, "
            "e.g. 'summarize file then save', 'search then explain'.\n"
            "  Planner + LLM + tools.\n\n"
            "ROUTE UNKNOWN — greeting, vague input, social chitchat, unclear.\n"
            "  Ask one clarifying question.\n\n"
            "RULES:\n"
            "- Translation, summarization, explanation, code generation are ALWAYS KNOWLEDGE.\n"
            "- Single desktop actions are DESKTOP_ACTION.\n"
            "- Multiple-step tasks combining reading/analysis + file ops are MIXED_TASK.\n"
            "- NEVER route write-code or pure Q&A as anything except KNOWLEDGE."
        )
        prompt = (
            f"Tools:\n{tools_desc}\n\n"
            f"Request: \"{text}\"\n\n"
            f"Reply EXACTLY:\n"
            f"ROUTE|explanation|tool_name_if_desktop_action\n\n"
            f"Examples:\n"
            f"KNOWLEDGE|User asked what Python is — definition question|\n"
            f"DESKTOP_ACTION|User wants to open Chrome|browser\n"
            f"MIXED_TASK|Read file then summarize — multi-step|\n"
            f"UNKNOWN|Greeting — no action requested|"
        )
        result = await self.ollama.generate(prompt, system=sys)
        result = result.strip()
        parts = result.split("|", 2)
        if len(parts) >= 2:
            route_str = parts[0].strip().upper()
            explanation = parts[1].strip() if len(parts) > 1 else ""
            tool_name = parts[2].strip() if len(parts) > 2 else ""
            route_map = {
                "KNOWLEDGE": Route.KNOWLEDGE,
                "DESKTOP_ACTION": Route.DESKTOP_ACTION,
                "MIXED_TASK": Route.MIXED_TASK,
                "UNKNOWN": Route.UNKNOWN,
            }
            route = route_map.get(route_str)
            if route:
                return IntentRouteResult(
                    route=route, original_text=text,
                    explanation=explanation or f"LLM classified as {route.value}",
                    confidence=0.8,
                    requires_planning=route in (Route.DESKTOP_ACTION, Route.MIXED_TASK),
                    requires_tools=route in (Route.DESKTOP_ACTION, Route.MIXED_TASK),
                    suggested_tool=tool_name if tool_name else None,
                )
        return None
