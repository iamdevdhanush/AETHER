"""
AETHER Git Tool
Execute Git commands and return structured output.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from shutil import which

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class GitPlugin(ToolBase):

    def name(self) -> str:
        return "git"

    def description(self) -> str:
        return "Execute Git commands: status, commit, push, pull, log, add, clone, branch, and more"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Git command and args (e.g. status, pull, commit -m 'msg')"},
                "path": {"type": "string", "description": "Working directory"},
            },
            "required": ["input"],
        }

    def initialize(self):
        self._git_path = which("git")
        if self._git_path:
            logger.info("Git found at: %s", self._git_path)
        else:
            logger.warning("Git CLI not found")

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        if not self._git_path:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr="Git not found in PATH. Install from https://git-scm.com", exit_code=1, success=False, execution_time_ms=elapsed)

        args = params.get("input", "").strip()
        workdir = params.get("path") or params.get("cwd") or str(Path.cwd())

        if not args:
            args = "status"

        return await self._run_git(args, workdir, start)

    async def _run_git(self, args: str, workdir: str, start: float) -> ToolObservation:
        cmd = f"{self._git_path} {args}"
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=workdir, shell=True)
            else:
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=workdir, executable="/bin/bash")
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                proc.kill()
                elapsed = (time.time() - start) * 1000
                return ToolObservation(stdout="", stderr="Git command timed out.", exit_code=-1, success=False, execution_time_ms=elapsed)

            elapsed = (time.time() - start) * 1000
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            return ToolObservation(stdout=stdout_str, stderr=stderr_str, exit_code=proc.returncode or 0, success=proc.returncode == 0, execution_time_ms=elapsed)
        except FileNotFoundError:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr="Git command not found.", exit_code=1, success=False, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Git error: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        logger.info("Git tool shut down")
