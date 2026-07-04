"""
AETHER System Plugin
System power actions and screen capture.
"""

import asyncio
import logging
import sys
import subprocess
from pathlib import Path
from datetime import datetime

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class SystemPlugin(PluginBase):

    def initialize(self):
        logger.info("System plugin initialized")

    async def execute(self, payload: dict) -> str:
        input_str = payload.get("input", "").strip().lower()

        if "screenshot" in input_str or "capture" in input_str:
            return await self._take_screenshot()

        if "shutdown" in input_str:
            return await self._power_action("shutdown")

        if "restart" in input_str or "reboot" in input_str:
            return await self._power_action("restart")

        if "sleep" in input_str:
            return await self._power_action("sleep")

        if "hibernate" in input_str:
            return await self._power_action("hibernate")

        if "lock" in input_str:
            return await self._power_action("lock")

        if "logoff" in input_str or "logout" in input_str:
            return await self._power_action("logoff")

        return (
            "Available system commands:\n"
            "  - screenshot / capture screen\n"
            "  - shutdown\n"
            "  - restart / reboot\n"
            "  - sleep\n"
            "  - hibernate\n"
            "  - lock\n"
            "  - logoff / logout"
        )

    async def _take_screenshot(self) -> str:
        shot_dir = Path.home() / "Pictures" / "AETHER_screenshots"
        shot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = shot_dir / f"screenshot_{timestamp}.png"

        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "powershell",
                    "-Command",
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds | "
                    f"ForEach-Object {{ "
                    f"  $bmp = New-Object System.Drawing.Bitmap $_.Width, $_.Height; "
                    f"  $gfx = [System.Drawing.Graphics]::FromImage($bmp); "
                    f"  $gfx.CopyFromScreen($_.X, $_.Y, 0, 0, "
                    f"    $bmp.Size, [System.Drawing.CopyPixelOperation]::SourceCopy); "
                    f"  $bmp.Save('{filename}'); "
                    f"  $gfx.Dispose(); $bmp.Dispose(); "
                    f"}}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=15.0,
                )
                if filename.exists():
                    return f"Screenshot saved: {filename}"
                error = stderr.decode("utf-8", errors="replace").strip()
                return f"Screenshot failed: {error or 'unknown error'}"

            elif sys.platform == "darwin":
                proc = await asyncio.create_subprocess_exec(
                    "screencapture", str(filename),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                if filename.exists():
                    return f"Screenshot saved: {filename}"
                return "Screenshot failed"

            else:
                proc = await asyncio.create_subprocess_exec(
                    "gnome-screenshot", "-f", str(filename),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                if filename.exists():
                    return f"Screenshot saved: {filename}"
                return "Screenshot failed (try installing gnome-screenshot)"

        except Exception as e:
            logger.error("Screenshot error: %s", e)
            return f"Screenshot error: {e}"

    async def _power_action(self, action: str) -> str:
        confirm_msg = {
            "shutdown": "Shutting down system...",
            "restart": "Restarting system...",
            "sleep": "Putting system to sleep...",
            "hibernate": "Hibernating system...",
            "lock": "Locking workstation...",
            "logoff": "Logging off...",
        }.get(action, f"Executing {action}...")

        try:
            if sys.platform == "win32":
                cmds = {
                    "shutdown": ["shutdown", "/s", "/t", "5"],
                    "restart": ["shutdown", "/r", "/t", "5"],
                    "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"],
                    "hibernate": ["rundll32.exe", "powrprof.dll,SetSuspendState", "Hibernate"],
                    "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
                    "logoff": ["shutdown", "/l"],
                }
                cmd = cmds.get(action)
                if not cmd:
                    return f"Unknown action: {action}"

                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    close_fds=True,
                )

            elif sys.platform == "darwin":
                cmds = {
                    "shutdown": ["osascript", "-e", 'tell app "System Events" to shut down'],
                    "restart": ["osascript", "-e", 'tell app "System Events" to restart'],
                    "sleep": ["pmset", "sleepnow"],
                    "lock": ["osascript", "-e", 'tell app "System Events" to sleep'],
                    "logoff": ["osascript", "-e", 'tell app "System Events" to log out'],
                }
                cmd = cmds.get(action)
                if cmd:
                    subprocess.Popen(cmd, start_new_session=True)

            else:
                cmds = {
                    "shutdown": ["systemctl", "poweroff"],
                    "restart": ["systemctl", "reboot"],
                    "sleep": ["systemctl", "suspend"],
                    "hibernate": ["systemctl", "hibernate"],
                    "lock": ["loginctl", "lock-session"],
                    "logoff": ["loginctl", "terminate-user", str(Path.home().name)],
                }
                cmd = cmds.get(action)
                if cmd:
                    subprocess.Popen(cmd, start_new_session=True)

            return confirm_msg

        except Exception as e:
            logger.error("Power action %s failed: %s", action, e)
            return f"Failed to {action}: {e}"

    def shutdown(self):
        logger.info("System plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "system",
            "description": "System power actions: shutdown, restart, sleep, lock, screenshot",
            "version": "1.0.0",
            "icon": "⚙️",
            "category": "system",
        }
