"""
AETHER Terminal Tool
Execute shell commands and return structured output.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class TerminalPlugin(ToolBase):

    def name(self) -> str:
        return "terminal"

    def description(self) -> str:
        return "Execute shell commands and return output"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory"},
            },
            "required": ["input"],
        }

    def initialize(self):
        self._shell = sys.platform == "win32"
        self._cwd = str(Path.home())

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        command = params.get("input", "").strip()
        cwd = params.get("cwd", self._cwd)

        if not command:
            return ToolObservation(stdout="", stderr="No command provided.", exit_code=1, success=False)

        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(
                    command, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, cwd=cwd, shell=True,
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    command, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, cwd=cwd, executable="/bin/bash",
                )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                proc.kill()
                elapsed = (time.time() - start) * 1000
                return ToolObservation(stdout="", stderr="Command timed out after 30 seconds.", exit_code=-1, success=False, execution_time_ms=elapsed)

            elapsed = (time.time() - start) * 1000
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            success = proc.returncode == 0

            return ToolObservation(
                stdout=stdout_str, stderr=stderr_str,
                exit_code=proc.returncode or 0, success=success,
                execution_time_ms=elapsed,
                system_changes=[command] if success and self._is_mutating(command) else [],
            )
        except FileNotFoundError as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Command not found: {e}", exit_code=1, success=False, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error("Terminal error: %s", e, exc_info=True)
            return ToolObservation(stdout="", stderr=f"Error: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def _is_mutating(self, cmd: str) -> bool:
        mutating = ["rm ", "mv ", "cp ", "mkdir ", "touch ", "chmod ", "chown ", ">", "|", "apt", "pip", "npm"]
        return any(m in cmd for m in mutating)

    def shutdown(self):
        logger.info("Terminal tool shut down")
