"""
AETHER File System Plugin
Browse, read, write, and manage files.
"""

import asyncio
import logging
import json
import os
import shutil
from pathlib import Path
from datetime import datetime

import aiofiles

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class FilesystemPlugin(PluginBase):
    """
    File system operations: list, read, write, delete, move, stat.
    """

    def initialize(self):
        self._home = Path.home()
        logger.info("Filesystem plugin initialized")

    async def execute(self, payload: dict) -> str:
        action = payload.get("action", "list")
        path_str = payload.get("path", str(self._home))
        content = payload.get("content", "")

        path = Path(path_str).expanduser().resolve()

        try:
            if action == "list":
                return await self._list(path)
            elif action == "read":
                return await self._read(path)
            elif action == "write":
                return await self._write(path, content)
            elif action == "delete":
                return await self._delete(path)
            elif action == "stat":
                return await self._stat(path)
            elif action == "mkdir":
                return await self._mkdir(path)
            elif action == "search":
                query = payload.get("query", "")
                return await self._search(path, query)
            else:
                # Default: parse input string for action
                return await self._parse_and_execute(payload.get("input", ""))
        except PermissionError:
            return f"Permission denied: {path}"
        except FileNotFoundError:
            return f"Not found: {path}"
        except Exception as e:
            logger.error(f"Filesystem error: {e}", exc_info=True)
            return f"Error: {e}"

    async def _parse_and_execute(self, input_str: str) -> str:
        """Parse natural-language-ish input like 'list /home' or 'read file.txt'"""
        parts = input_str.strip().split(None, 1)
        if not parts:
            return await self._list(self._home)

        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else str(self._home)

        if cmd in ("ls", "list", "dir"):
            return await self._list(Path(arg).expanduser().resolve())
        elif cmd in ("cat", "read", "open"):
            return await self._read(Path(arg).expanduser().resolve())
        elif cmd == "stat":
            return await self._stat(Path(arg).expanduser().resolve())
        elif cmd == "mkdir":
            return await self._mkdir(Path(arg).expanduser().resolve())
        else:
            return await self._list(self._home)

    async def _list(self, path: Path) -> str:
        if not path.exists():
            return f"Path does not exist: {path}"
        if path.is_file():
            return await self._stat(path)

        entries = []
        try:
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            for item in items[:200]:
                try:
                    stat = item.stat()
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    kind = "DIR " if item.is_dir() else "FILE"
                    size_str = self._format_size(size) if item.is_file() else "     "
                    entries.append(f"{kind}  {size_str:>8}  {modified}  {item.name}")
                except Exception:
                    entries.append(f"???   {item.name}")
        except PermissionError:
            return f"Permission denied: {path}"

        header = f"Directory: {path}\n{'─' * 60}"
        return header + "\n" + "\n".join(entries) if entries else f"{path} (empty)"

    async def _read(self, path: Path) -> str:
        if not path.is_file():
            return f"Not a file: {path}"

        # Size limit: 1 MB
        if path.stat().st_size > 1_048_576:
            return f"File too large to display (>{1}MB): {path}"

        async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        return f"File: {path}\n{'─' * 60}\n{content}"

    async def _write(self, path: Path, content: str) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return f"Written {len(content)} bytes to {path}"

    async def _delete(self, path: Path) -> str:
        if path.is_dir():
            shutil.rmtree(path)
            return f"Deleted directory: {path}"
        else:
            path.unlink()
            return f"Deleted file: {path}"

    async def _stat(self, path: Path) -> str:
        if not path.exists():
            return f"Not found: {path}"
        s = path.stat()
        kind = "Directory" if path.is_dir() else "File"
        return (
            f"{kind}: {path}\n"
            f"Size: {self._format_size(s.st_size)}\n"
            f"Modified: {datetime.fromtimestamp(s.st_mtime).isoformat()}\n"
            f"Created: {datetime.fromtimestamp(s.st_ctime).isoformat()}\n"
            f"Permissions: {oct(s.st_mode)}"
        )

    async def _mkdir(self, path: Path) -> str:
        path.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {path}"

    async def _search(self, base: Path, query: str) -> str:
        if not query:
            return "No search query provided."
        results = []
        try:
            for item in base.rglob(f"*{query}*"):
                results.append(str(item))
                if len(results) >= 50:
                    break
        except Exception as e:
            return f"Search error: {e}"
        if not results:
            return f"No files matching '{query}' in {base}"
        return f"Found {len(results)} matches:\n" + "\n".join(results)

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def shutdown(self):
        logger.info("Filesystem plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "filesystem",
            "description": "Browse and manage files and directories",
            "version": "1.0.0",
            "icon": "📁",
            "category": "system",
        }
