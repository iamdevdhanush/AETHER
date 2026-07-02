from __future__ import annotations
from typing import Any
from plugins.manager import BasePlugin
from services.automation import automation_service


class AutomationPlugin(BasePlugin):
    id = "automation"
    name = "Desktop Automation"
    description = "Launch, close, and control desktop applications"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "launch")
        name = kwargs.get("name", "")

        if action == "launch":
            return await automation_service.launch_app(name)
        elif action == "close":
            return await automation_service.close_app(name)
        elif action == "command":
            return await automation_service.system_command(kwargs.get("command", ""))
        return {"success": False, "error": f"Unknown action: {action}"}
