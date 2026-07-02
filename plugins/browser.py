from __future__ import annotations
import asyncio
from typing import Any
from plugins.manager import BasePlugin


class BrowserPlugin(BasePlugin):
    id = "browser"
    name = "Browser Control"
    description = "Open URLs and control web browser"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        import webbrowser
        action = kwargs.get("action", "open")
        url = kwargs.get("url", "https://google.com")

        if action == "open":
            webbrowser.open(url)
            return {"success": True, "url": url}
        return {"success": False, "error": f"Unknown action: {action}"}
