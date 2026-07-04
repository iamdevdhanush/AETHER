"""
AETHER System Tool
System power actions and screen capture.
"""

import asyncio
import logging
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class SystemPlugin(ToolBase):

    def name(self) -> str:
        return "system"

    def description(self) -> str:
        return "System power actions: shutdown, restart, sleep, lock, screenshot, hibernate"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Action: shutdown, restart, sleep, hibernate, lock, screenshot"},
            },
            "required": ["input"],
        }

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        input_str = params.get("input", "").strip().lower()

        if "screenshot" in input_str or "capture" in input_str:
            return await self._take_screenshot(start)
        if "shutdown" in input_str:
            return await self._power_action("shutdown", start)
        if "restart" in input_str or "reboot" in input_str:
            return await self._power_action("restart", start)
        if "sleep" in input_str:
            return await self._power_action("sleep", start)
        if "hibernate" in input_str:
            return await self._power_action("hibernate", start)
        if "lock" in input_str:
            return await self._power_action("lock", start)
        if "logoff" in input_str or "logout" in input_str:
            return await self._power_action("logoff", start)

        elapsed = (time.time() - start) * 1000
        return ToolObservation(
            stdout="Available: screenshot, shutdown, restart, sleep, hibernate, lock, logoff",
            exit_code=0, success=True, execution_time_ms=elapsed,
        )

    async def _take_screenshot(self, start: float) -> ToolObservation:
        shot_dir = Path.home() / "Pictures" / "AETHER_screenshots"
        shot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = shot_dir / f"screenshot_{timestamp}.png"

        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "powershell", "-Command",
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds | "
                    f"ForEach-Object {{ $bmp = New-Object System.Drawing.Bitmap $_.Width, $_.Height; "
                    f"$gfx = [System.Drawing.Graphics]::FromImage($bmp); "
                    f"$gfx.CopyFromScreen($_.X, $_.Y, 0, 0, $bmp.Size, "
                    f"[System.Drawing.CopyPixelOperation]::SourceCopy); "
                    f"$bmp.Save('{filename}'); $gfx.Dispose(); $bmp.Dispose(); }}",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
                elapsed = (time.time() - start) * 1000
                if filename.exists():
                    return ToolObservation(stdout=f"Screenshot saved: {filename}", exit_code=0, success=True, execution_time_ms=elapsed)
                return ToolObservation(stdout="", stderr=stderr.decode(), exit_code=1, success=False, execution_time_ms=elapsed)
            elif sys.platform == "darwin":
                proc = await asyncio.create_subprocess_exec("screencapture", str(filename))
                await proc.wait()
                elapsed = (time.time() - start) * 1000
                if filename.exists():
                    return ToolObservation(stdout=f"Screenshot saved: {filename}", exit_code=0, success=True, execution_time_ms=elapsed)
                return ToolObservation(stdout="", stderr="Screenshot failed", exit_code=1, success=False, execution_time_ms=elapsed)
            else:
                proc = await asyncio.create_subprocess_exec("gnome-screenshot", "-f", str(filename))
                await proc.wait()
                elapsed = (time.time() - start) * 1000
                if filename.exists():
                    return ToolObservation(stdout=f"Screenshot saved: {filename}", exit_code=0, success=True, execution_time_ms=elapsed)
                return ToolObservation(stdout="", stderr="Screenshot failed", exit_code=1, success=False, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Screenshot error: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    async def _power_action(self, action: str, start: float) -> ToolObservation:
        confirm_msg = {"shutdown": "Shutting down...", "restart": "Restarting...",
                       "sleep": "Sleeping...", "hibernate": "Hibernating...",
                       "lock": "Locking...", "logoff": "Logging off..."}.get(action, f"{action}...")
        try:
            if sys.platform == "win32":
                cmds = {"shutdown": ["shutdown", "/s", "/t", "5"],
                        "restart": ["shutdown", "/r", "/t", "5"],
                        "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"],
                        "hibernate": ["rundll32.exe", "powrprof.dll,SetSuspendState", "Hibernate"],
                        "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
                        "logoff": ["shutdown", "/l"]}
                cmd = cmds.get(action)
                if cmd:
                    subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
            elif sys.platform == "darwin":
                cmds = {"shutdown": ["osascript", "-e", 'tell app "System Events" to shut down'],
                        "restart": ["osascript", "-e", 'tell app "System Events" to restart'],
                        "sleep": ["pmset", "sleepnow"],
                        "lock": ["osascript", "-e", 'tell app "System Events" to sleep'],
                        "logoff": ["osascript", "-e", 'tell app "System Events" to log out']}
                cmd = cmds.get(action)
                if cmd:
                    subprocess.Popen(cmd, start_new_session=True)
            else:
                cmds = {"shutdown": ["systemctl", "poweroff"], "restart": ["systemctl", "reboot"],
                        "sleep": ["systemctl", "suspend"], "hibernate": ["systemctl", "hibernate"],
                        "lock": ["loginctl", "lock-session"],
                        "logoff": ["loginctl", "terminate-user", str(Path.home().name)]}
                cmd = cmds.get(action)
                if cmd:
                    subprocess.Popen(cmd, start_new_session=True)
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout=confirm_msg, exit_code=0, success=True, execution_time_ms=elapsed, system_changes=[f"system:{action}"])
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Failed to {action}: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        logger.info("System tool shut down")
