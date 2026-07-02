from __future__ import annotations
import asyncio
import subprocess
import sys
from core.security import security_manager, Permission


class DesktopAutomationService:
    async def launch_app(self, name: str) -> dict:
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "cmd", "/c", "start", "", name,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            elif sys.platform == "darwin":
                proc = await asyncio.create_subprocess_exec(
                    "open", "-a", name,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    name, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            return {"success": True, "app": name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_app(self, name: str) -> dict:
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "taskkill", "/IM", name, "/F",
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    "pkill", "-f", name,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            return {"success": True, "app": name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def system_command(self, command: str) -> dict:
        valid, msg = security_manager.validate_command(command)
        if not valid:
            return {"success": False, "error": msg}
        if not security_manager.require(Permission.EXECUTE_COMMANDS):
            return {"success": False, "error": "Execute commands permission not granted"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


automation_service = DesktopAutomationService()
