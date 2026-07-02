from __future__ import annotations
from pathlib import Path
from typing import Any
from plugins.manager import BasePlugin
from services.file_operations import file_service


class FileSystemPlugin(BasePlugin):
    id = "filesystem"
    name = "File System"
    description = "Browse, read, and manage files on the local system"
    version = "0.1.0"

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "list")
        path = kwargs.get("path", ".")

        if action == "list":
            return await file_service.list_directory(path)
        elif action == "read":
            return await file_service.read_file(path)
        elif action == "exists":
            return {"success": True, "exists": Path(path).exists()}
        return {"success": False, "error": f"Unknown action: {action}"}

    def settings(self) -> dict:
        return {
            "max_file_size": 10485760,
            "allowed_extensions": [".txt", ".md", ".py", ".js", ".ts", ".json"],
        }
