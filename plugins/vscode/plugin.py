"""
AETHER VS Code Plugin
Launch VS Code with a file or directory.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from shutil import which

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class VSCodePlugin(PluginBase):
    """
    Launches Visual Studio Code for a given path.
    Supports both the `code` CLI and common installation paths.
    """

    def initialize(self):
        self._code_path = self._find_vscode()
        if self._code_path:
            logger.info(f"VS Code found at: {self._code_path}")
        else:
            logger.warning("VS Code not found in PATH or default locations")

    def _find_vscode(self) -> str | None:
        """Find the VS Code executable."""
        # Check PATH first
        if which("code"):
            return "code"

        # Windows default install paths
        if sys.platform == "win32":
            candidates = [
                Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe",
                Path("C:/Program Files/Microsoft VS Code/Code.exe"),
                Path("C:/Program Files (x86)/Microsoft VS Code/Code.exe"),
            ]
            for p in candidates:
                if p.exists():
                    return str(p)

        # macOS
        if sys.platform == "darwin":
            candidates = [
                Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
                Path("/usr/local/bin/code"),
            ]
            for p in candidates:
                if p.exists():
                    return str(p)

        # Linux
        for name in ("code", "code-oss", "vscodium"):
            path = which(name)
            if path:
                return path

        return None

    async def execute(self, payload: dict) -> str:
        path_str = payload.get("input", "").strip() or payload.get("path", "").strip()

        if not self._code_path:
            return (
                "VS Code not found. Install it from https://code.visualstudio.com "
                "and ensure 'code' is in your PATH."
            )

        if not path_str:
            # Open VS Code without a specific file
            target_path = None
        else:
            target = Path(path_str).expanduser().resolve()
            if not target.exists():
                return f"Path does not exist: {target}"
            target_path = str(target)

        try:
            cmd = [self._code_path]
            if target_path:
                cmd.append(target_path)

            if sys.platform == "win32":
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    cmd,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            msg = f"Opened VS Code"
            if target_path:
                msg += f": {target_path}"
            return msg

        except Exception as e:
            logger.error(f"VS Code launch error: {e}")
            return f"Failed to launch VS Code: {e}"

    def shutdown(self):
        logger.info("VS Code plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "vscode",
            "description": "Open files and projects in Visual Studio Code",
            "version": "1.0.0",
            "icon": "💻",
            "category": "dev",
        }
