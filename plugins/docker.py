from __future__ import annotations
import asyncio
import subprocess
from typing import Any
from plugins.manager import BasePlugin


class DockerPlugin(BasePlugin):
    id = "docker"
    name = "Docker"
    description = "Manage Docker containers and images"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "ps")
        cmd = ["docker"]

        if action == "ps":
            cmd.extend(["ps", "-a"])
        elif action == "images":
            cmd.append("images")
        elif action == "logs":
            cmd.extend(["logs", kwargs.get("container", ""), "--tail", str(kwargs.get("lines", 50))])
        elif action == "info":
            cmd.append("info")
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace"),
                "error": stderr.decode(errors="replace"),
            }
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found. Is Docker installed?"}
        except Exception as e:
            return {"success": False, "error": str(e)}
