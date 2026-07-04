"""
AETHER Git Plugin
Execute Git commands and return output.
"""

import asyncio
import logging
import sys
from pathlib import Path
from shutil import which

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class GitPlugin(PluginBase):

    def initialize(self):
        self._git_path = which("git")
        if self._git_path:
            logger.info("Git found at: %s", self._git_path)
        else:
            logger.warning("Git CLI not found")

    async def execute(self, payload: dict) -> str:
        if not self._git_path:
            return (
                "Git not found in PATH. Install git from "
                "https://git-scm.com/downloads"
            )

        input_str = payload.get("input", "").strip()
        workdir = payload.get("path") or payload.get("cwd") or str(Path.cwd())

        return await self._run_git(input_str, workdir)

    async def _run_git(self, args: str, workdir: str) -> str:
        if not args:
            args = "status"

        cmd = f"{self._git_path} {args}"
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workdir,
                    shell=True,
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workdir,
                    executable="/bin/bash",
                )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=30.0,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return "Git command timed out after 30 seconds."

            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(
                    f"[stderr]\n{stderr.decode('utf-8', errors='replace')}",
                )

            result = "\n".join(output_parts).strip()
            return result or f"(exit code: {proc.returncode})"

        except FileNotFoundError:
            return "Git command not found."
        except Exception as e:
            logger.error("Git error: %s", e, exc_info=True)
            return f"Git error: {e}"

    def shutdown(self):
        logger.info("Git plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "git",
            "description": "Execute Git commands: status, commit, push, pull, log, and more",
            "version": "1.0.0",
            "icon": "🔀",
            "category": "dev",
        }
