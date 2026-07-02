from __future__ import annotations
from typing import Any
from plugins.manager import BasePlugin
from services.system_monitor import SystemMonitorService


class SystemPlugin(BasePlugin):
    id = "system"
    name = "System Monitor"
    description = "Monitor CPU, GPU, RAM, disk, battery, and network"
    version = "0.1.0"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = SystemMonitorService()

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "metrics")
        if action == "metrics":
            return self._monitor.get_metrics()
        return {"success": False, "error": f"Unknown action: {action}"}
