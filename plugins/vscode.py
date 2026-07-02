from __future__ import annotations
import asyncio
import subprocess
from typing import Any
from plugins.manager import BasePlugin


class VSCodePlugin(BasePlugin):
    id = "vscode"
    name = "VS Code"
    description = "Open files and folders in VS Code"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "open")
        path = kwargs.get("path", ".")

        if action == "open":
            proc = await asyncio.create_subprocess_exec(
                "code", path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await proc.wait()
            return {"success": proc.returncode == 0, "path": path}
        return {"success": False, "error": f"Unknown action: {action}"}
