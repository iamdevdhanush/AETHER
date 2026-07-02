from __future__ import annotations
import asyncio
import subprocess
import sys
from typing import Any
from plugins.manager import BasePlugin


class TerminalPlugin(BasePlugin):
    id = "terminal"
    name = "Terminal"
    description = "Execute terminal commands and capture output"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        command = kwargs.get("command", "")
        if not command:
            return {"success": False, "error": "No command provided"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
                "exit_code": proc.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
