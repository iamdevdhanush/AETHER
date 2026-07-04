"""
AETHER Intent Engine
Classifies user input into structured intents.
Fast path: keyword/pattern matching.
Slow path: Ollama-based classification for ambiguous inputs.
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    type: str  # "tool" | "question" | "chat"
    plugin: Optional[str] = None  # tool name if type == "tool"
    args: dict = field(default_factory=dict)
    confidence: float = 0.0
    explanation: str = ""


TOOL_SIGNATURES = {
    "browser": {
        "triggers": [
            "open", "go to", "navigate to", "search for", "browse",
            "launch browser", "website", "url", "google",
        ],
        "description": "Open URLs or search the web in default browser",
    },
    "vscode": {
        "triggers": [
            "vs code", "visual studio code", "vscode", "open in code",
            "launch code", "start code", "code editor",
        ],
        "description": "Open files and projects in Visual Studio Code",
    },
    "terminal": {
        "triggers": [
            "run", "execute", "command", "terminal", "shell",
            "run command", "execute command",
        ],
        "description": "Execute shell commands and return output",
    },
    "filesystem": {
        "triggers": [
            "create folder", "create directory", "make directory",
            "make folder", "list files", "read file", "delete file",
            "delete folder", "write file", "save file", "mkdir",
            "show directory", "list directory",
        ],
        "description": "Browse and manage files and directories",
    },
    "executor": {
        "triggers": [
            "run python", "execute code", "run code", "python script",
            "run script", "execute python",
        ],
        "description": "Execute Python code snippets",
    },
    "sysmon": {
        "triggers": [
            "system status", "system info", "cpu", "memory", "ram",
            "disk", "battery", "network", "process", "stats",
            "performance", "system information",
        ],
        "description": "Detailed system statistics: CPU, RAM, disk, network, processes",
    },
    "docker": {
        "triggers": [
            "docker", "container", "image", "docker ps", "docker run",
            "docker stop", "docker start", "docker pull",
        ],
        "description": "Manage Docker containers and images",
    },
    "git": {
        "triggers": [
            "git", "git status", "git pull", "git push", "git commit",
            "git add", "git log", "git clone", "git branch",
        ],
        "description": "Git operations: commit, push, pull, status, log",
    },
    "system": {
        "triggers": [
            "shutdown", "restart", "reboot", "sleep", "hibernate",
            "lock computer", "screenshot", "take screenshot",
        ],
        "description": "System power actions and screen capture",
    },
}

TOOL_ARG_PATTERNS: dict[str, list[tuple[re.Pattern, str, str]]] = {
    "browser": [
        (re.compile(r"(?:open|go\s+to|navigate\s+to|launch)\s+(.+?)(?:\s*)$", re.I), "input", "url"),
        (re.compile(r"search\s+(?:for\s+)?(.+?)(?:\s*)$", re.I), "input", "query"),
    ],
    "vscode": [
        (re.compile(r"(?:open|launch|start)\s+(.+?)(?:\s+(?:in|with)\s+(?:vs\s*code|visual\s+studio))?(?:\s*)$", re.I), "input", "path"),
    ],
    "terminal": [
        (re.compile(r"(?:run|execute)\s+(.+?)(?:\s*)$", re.I), "input", "command"),
    ],
    "filesystem": [
        (re.compile(r"(?:create|make)\s+(?:folder|directory)\s+(.+?)(?:\s*)$", re.I), "input", f"mkdir {{path}}"),
        (re.compile(r"(?:list|show)\s+(?:files|directory|folder|dir)\s+(.+?)(?:\s*)$", re.I), "input", f"list {{path}}"),
        (re.compile(r"(?:read|open|show)\s+(?:file\s+)?(.+?)(?:\s*)$", re.I), "input", f"read {{path}}"),
        (re.compile(r"(?:delete|remove)\s+(?:file\s+)?(.+?)(?:\s*)$", re.I), "input", f"delete {{path}}"),
    ],
    "executor": [],
    "sysmon": [],
    "docker": [
        (re.compile(r"(?:(?:run|execute)\s+)?docker\s+(.+?)(?:\s*)$", re.I), "input", "docker command"),
    ],
    "git": [
        (re.compile(r"(?:(?:run|execute)\s+)?git\s+(.+?)(?:\s*)$", re.I), "input", "git command"),
    ],
    "system": [],
}

QUESTION_PATTERNS = re.compile(
    r"^(what|why|when|where|who|how|is|are|was|were|do|does|did|can|could|would|should|will|shall|has|have|had|tell|explain|define|describe|show)\b",
    re.I,
)


class IntentEngine:

    def __init__(self, ollama=None):
        self.ollama = ollama

    async def classify(self, text: str) -> Intent:
        text = text.strip()
        if not text:
            return Intent(type="chat", confidence=1.0, explanation="Empty input")

        intent = self._fast_path(text)
        if intent.confidence >= 0.65:
            logger.info(
                "Fast path classified as %s (plugin=%s, conf=%.2f)",
                intent.type, intent.plugin, intent.confidence,
            )
            return intent

        if self.ollama:
            try:
                ollama_intent = await self._ollama_classify(text)
                if ollama_intent and ollama_intent.confidence > intent.confidence:
                    logger.info(
                        "Ollama classified as %s (plugin=%s, conf=%.2f)",
                        ollama_intent.type, ollama_intent.plugin, ollama_intent.confidence,
                    )
                    return ollama_intent
            except Exception as e:
                logger.warning("Ollama intent classification failed: %s", e)

        logger.info("Fallback classified as %s (conf=%.2f)", intent.type, intent.confidence)
        return intent

    def _fast_path(self, text: str) -> Intent:
        text_lower = text.lower().strip()
        best_tool = None
        best_score = 0.0
        best_trigger = ""

        for tool_name, sig in TOOL_SIGNATURES.items():
            for trigger in sig["triggers"]:
                if trigger in text_lower:
                    score = len(trigger) / max(len(text_lower), 1)
                    if text_lower.startswith(trigger):
                        score += 0.2
                    if score > best_score:
                        best_score = score
                        best_tool = tool_name
                        best_trigger = trigger

        if best_tool and best_score >= 0.3:
            args = self._extract_args_fast(text, best_tool)
            return Intent(
                type="tool",
                plugin=best_tool,
                args=args,
                confidence=min(best_score + 0.2, 1.0),
                explanation=f"Execute {best_tool}: {best_trigger}",
            )

        if re.search(r"(?:^|\s)\?\s*$", text_lower) or text_lower.endswith("?"):
            return Intent(
                type="question",
                confidence=0.7,
                explanation="Direct question detected",
            )

        if QUESTION_PATTERNS.match(text_lower):
            return Intent(
                type="question",
                confidence=0.6,
                explanation="Knowledge question",
            )

        return Intent(
            type="chat",
            confidence=0.3,
            explanation="General conversation",
        )

    def _extract_args_fast(self, text: str, tool_name: str) -> dict:
        patterns = TOOL_ARG_PATTERNS.get(tool_name, [])
        for pattern, arg_key, _ in patterns:
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if value:
                    return {arg_key: value}
        return {}

    async def _ollama_classify(self, text: str) -> Optional[Intent]:
        if not self.ollama:
            return None

        tool_list = "\n".join(
            f"  - {name}: {sig['description']}"
            for name, sig in TOOL_SIGNATURES.items()
        )

        prompt = (
            f"Classify this user request into one of these categories:\n\n"
            f"Available tools:\n{tool_list}\n\n"
            f"Categories:\n"
            f"  - tool: A tool can perform the request. Specify which tool.\n"
            f"  - question: The user is asking for information or knowledge.\n"
            f"  - chat: General conversation, greeting, or anything else.\n\n"
            f"User request: \"{text}\"\n\n"
            f"Respond with EXACTLY one line in this format:\n"
            f"category|tool_name|brief explanation\n\n"
            f"Examples:\n"
            f"  Open Google → tool|browser|open google.com\n"
            f"  What is Python? → question||asking about Python\n"
            f"  Hello → chat||greeting"
        )

        result = await self.ollama.generate(prompt, system="You classify user intent precisely. Respond in exact format requested.")
        result = result.strip()

        parts = result.split("|", 2)
        if len(parts) >= 2:
            category = parts[0].strip().lower()
            tool_name = parts[1].strip() if len(parts) > 1 else ""
            explanation = parts[2].strip() if len(parts) > 2 else ""

            if category == "tool" and tool_name:
                plugin = self.plugin_name_for_tool(tool_name)
                if plugin:
                    return Intent(
                        type="tool",
                        plugin=plugin,
                        confidence=0.85,
                        explanation=explanation or f"Execute {plugin}",
                    )

            if category == "question":
                return Intent(
                    type="question",
                    confidence=0.85,
                    explanation=explanation or "Knowledge question",
                )

        return Intent(
            type="chat",
            confidence=0.7,
            explanation="Ollama defaulted to chat",
        )

    @staticmethod
    def plugin_name_for_tool(tool_name: str) -> Optional[str]:
        tool_lower = tool_name.lower().strip()
        for key in TOOL_SIGNATURES:
            if tool_lower == key:
                return key
            if tool_lower in TOOL_SIGNATURES[key]["triggers"]:
                return key
        return None
