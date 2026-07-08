"""
AETHER Reflection Engine
After every action, evaluates success and decides next steps.
Never asks the user for help — retries intelligently with alternative approaches.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ReflectionEngine:

    def __init__(self, ollama=None):
        self.ollama = ollama

    async def reflect(self, tool_name: str, observation: dict,
                      step_description: str) -> tuple[str, str]:
        """
        Evaluate tool execution result.
        Returns (reflection_text, action) where action is one of:
          "continue" — success, proceed to next step
          "retry"    — failed, try again with same params
          "retry_alt" — failed, try a different tool/approach
          "skip"     — non-critical failure, skip this step
          "blocked"  — cannot proceed, need human intervention
        """
        success = observation.get("success", False)
        exit_code = observation.get("exit_code", 0)
        stderr = observation.get("stderr", "")

        if success:
            return f"Step completed successfully.", "continue"

        if self.ollama:
            try:
                return await self._llm_reflect(tool_name, observation, step_description)
            except Exception as e:
                logger.warning("LLM reflection failed: %s", e)

        return self._rule_based_reflect(tool_name, exit_code, stderr)

    def _rule_based_reflect(self, tool_name: str, exit_code: int,
                            stderr: str) -> tuple[str, str]:
        if exit_code != 0:
            if "not found" in stderr.lower() or "no such" in stderr.lower():
                return f"Resource not found. Cannot proceed.", "skip"
            if "permission" in stderr.lower() or "access" in stderr.lower():
                return f"Permission denied. Cannot proceed.", "skip"
            if "timeout" in stderr.lower():
                return f"Operation timed out. Retrying.", "retry"
            return f"Exit code {exit_code}. Retrying.", "retry"
        return f"Completed.", "continue"

    async def _llm_reflect(self, tool_name: str, observation: dict,
                            step_description: str) -> tuple[str, str]:
        prompt = (
            f"Evaluate this tool execution:\n\n"
            f"Step: {step_description}\n"
            f"Tool: {tool_name}\n"
            f"Success: {observation.get('success')}\n"
            f"Exit code: {observation.get('exit_code')}\n"
            f"stdout: {observation.get('stdout', '')[:200]}\n"
            f"stderr: {observation.get('stderr', '')[:200]}\n\n"
            f"Respond with one line:\n"
            f"reflection|action\n\n"
            f"Where action is: continue | retry | skip | blocked"
        )

        result = await self.ollama.generate(prompt, system="You evaluate tool execution results and decide next actions. Be decisive.")
        result = result.strip()
        parts = result.split("|", 1)
        reflection = parts[0].strip() if parts else "No reflection"
        action = parts[1].strip() if len(parts) > 1 else "retry"
        if action not in ("continue", "retry", "skip", "blocked"):
            action = "retry"
        return reflection, action
