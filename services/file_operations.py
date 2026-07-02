from __future__ import annotations
import os
import asyncio
from pathlib import Path
from core.security import security_manager, Permission


TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
    ".csv", ".xml", ".html", ".css", ".rs", ".go", ".java",
    ".c", ".cpp", ".h", ".hpp",
}


class FileService:
    async def read_file(self, path: str) -> dict:
        valid, msg = security_manager.validate_path(path)
        if not valid:
            return {"success": False, "error": msg}
        if not security_manager.require(Permission.FILE_OPERATIONS):
            return {"success": False, "error": "File operations permission not granted"}
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": "File not found"}
        suffix = p.suffix.lower()
        if suffix in TEXT_SUFFIXES:
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, lambda: p.read_text(encoding="utf-8", errors="replace"))
            return {"success": True, "content": content}
        elif suffix in (".pdf", ".docx"):
            return {"success": True, "content": f"[{suffix.upper()} file - preview not yet supported]"}
        else:
            return {"success": False, "error": f"Unsupported file type: {suffix}"}

    async def list_directory(self, path: str) -> dict:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            return {"success": False, "error": "Directory not found"}
        try:
            entries = []
            for entry in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": str(entry),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": stat.st_size if entry.is_file() else 0,
                })
            return {"success": True, "entries": entries}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}


file_service = FileService()
