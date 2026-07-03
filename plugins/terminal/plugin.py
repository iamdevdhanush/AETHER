"""
AETHER Terminal Plugin
Execute shell commands and return output.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class TerminalPlugin(PluginBase):
    """
    Execute shell commands asynchronously.
    Returns combined stdout/stderr output.
    """

    def initialize(self):
        self._shell = sys.platform == "win32"
        self._cwd = str(Path.home())
        logger.info(f"Terminal plugin initialized (cwd={self._cwd})")

    async def execute(self, payload: dict) -> str:
        command = payload.get("input", "").strip()
        cwd = payload.get("cwd", self._cwd)

        if not command:
            return "No command provided."

        logger.info(f"Terminal executing: {command}")

        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                    shell=True,
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                    executable="/bin/bash",
                )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=30.0
                )
            except asyncio.TimeoutError:
                proc.kill()
                return "Command timed out after 30 seconds."

            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(f"[stderr]\n{stderr.decode('utf-8', errors='replace')}")

            result = "\n".join(output_parts).strip()
            if not result:
                result = f"(exit code: {proc.returncode})"

            return result

        except FileNotFoundError as e:
            return f"Command not found: {e}"
        except Exception as e:
            logger.error(f"Terminal error: {e}", exc_info=True)
            return f"Error executing command: {e}"

    def shutdown(self):
        logger.info("Terminal plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "terminal",
            "description": "Execute shell commands and return output",
            "version": "1.0.0",
            "icon": "⌨️",
            "category": "system",
            "author": "AETHER",
        }

    def settings(self) -> dict:
        return {
            "timeout": {
                "type": "int",
                "default": 30,
                "description": "Command timeout in seconds",
            },
            "working_directory": {
                "type": "str",
                "default": str(Path.home()),
                "description": "Default working directory",
            },
        }
