import os
import shutil
from pathlib import Path
from loguru import logger
from app.core.security import security_manager, Permission


class FileService:
    async def read_file(self, path: str) -> dict:
        allowed, reason = security_manager.validate_path(path)
        if not allowed:
            return {"success": False, "error": reason}

        if not security_manager.require(Permission.FILE_OPERATIONS):
            return {"success": False, "error": "File operations not permitted"}

        try:
            filepath = Path(path)
            if not filepath.exists():
                return {"success": False, "error": "File not found"}

            suffixes = {".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".csv", ".xml", ".html", ".css", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".hpp"}
            if filepath.suffix in {".pdf", ".docx"}:
                # Placeholder for document parsing
                return {"success": True, "content": f"[{filepath.suffix} document] {filepath.name}"}

            if filepath.suffix in suffixes:
                content = await asyncio_get_content(filepath)
                return {"success": True, "content": content}

            return {"success": False, "error": f"Unsupported file type: {filepath.suffix}"}
        except Exception as e:
            logger.error(f"File read error: {e}")
            return {"success": False, "error": str(e)}

    async def list_directory(self, path: str) -> dict:
        try:
            dirpath = Path(path)
            if not dirpath.exists() or not dirpath.is_dir():
                return {"success": False, "error": "Directory not found"}

            entries = []
            for entry in dirpath.iterdir():
                entries.append({
                    "name": entry.name,
                    "path": str(entry.absolute()),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            return {"success": True, "entries": sorted(entries, key=lambda x: (x["type"] != "directory", x["name"]))}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def asyncio_get_content(filepath: Path) -> str:
    loop = asyncio_get_event_loop()
    return await loop.run_in_executor(None, lambda: filepath.read_text(encoding="utf-8", errors="replace"))


import asyncio
asyncio_get_event_loop = asyncio.get_event_loop


file_service = FileService()
