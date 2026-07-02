from __future__ import annotations
import asyncio
import subprocess
from typing import Any
from plugins.manager import BasePlugin


class GitHubPlugin(BasePlugin):
    id = "github"
    name = "GitHub"
    description = "Interact with GitHub via gh CLI"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "status")
        cmd = ["gh"]

        if action == "status":
            cmd.extend(["auth", "status"])
        elif action == "pr":
            cmd.extend(["pr", "list", "--limit", str(kwargs.get("limit", 10))])
        elif action == "issues":
            cmd.extend(["issue", "list", "--limit", str(kwargs.get("limit", 10))])
        elif action == "repo":
            cmd.extend(["repo", "view", kwargs.get("repo", ""), "--json", "name,description,url"])
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
            return {"success": False, "error": "GitHub CLI (gh) not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
