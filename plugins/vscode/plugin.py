"""
AETHER VS Code Tool
Launch VS Code with a file or directory.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path
from shutil import which

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class VSCodePlugin(ToolBase):

    def name(self) -> str:
        return "vscode"

    def description(self) -> str:
        return "Open files and projects in Visual Studio Code"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "File or directory path to open"},
            },
        }

    def initialize(self):
        self._code_path = self._find_vscode()
        if self._code_path:
            logger.info("VS Code found at: %s", self._code_path)
        else:
            logger.warning("VS Code not found in PATH or default locations")

    def _find_vscode(self) -> str | None:
        if which("code"):
            return "code"
        if sys.platform == "win32":
            candidates = [Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe",
                          Path("C:/Program Files/Microsoft VS Code/Code.exe"),
                          Path("C:/Program Files (x86)/Microsoft VS Code/Code.exe")]
            for p in candidates:
                if p.exists():
                    return str(p)
        if sys.platform == "darwin":
            candidates = [Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
                          Path("/usr/local/bin/code")]
            for p in candidates:
                if p.exists():
                    return str(p)
        for name in ("code", "code-oss", "vscodium"):
            path = which(name)
            if path:
                return path
        return None

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        path_str = params.get("input", "").strip() or params.get("path", "").strip()

        if not self._code_path:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr="VS Code not found. Install from https://code.visualstudio.com", exit_code=1, success=False, execution_time_ms=elapsed)

        target_path = None
        if path_str:
            target = Path(path_str).expanduser().resolve()
            if not target.exists():
                elapsed = (time.time() - start) * 1000
                return ToolObservation(stdout="", stderr=f"Path does not exist: {target}", exit_code=1, success=False, execution_time_ms=elapsed)
            target_path = str(target)

        try:
            cmd = [self._code_path]
            if target_path:
                cmd.append(target_path)

            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
            else:
                subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            elapsed = (time.time() - start) * 1000
            msg = f"Opened VS Code"
            if target_path:
                msg += f": {target_path}"
            return ToolObservation(stdout=msg, exit_code=0, success=True, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Failed to launch VS Code: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        logger.info("VS Code tool shut down")
