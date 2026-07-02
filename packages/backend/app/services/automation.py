import asyncio
import subprocess
import sys
from loguru import logger
from app.core.security import security_manager, Permission


class DesktopAutomationService:
    async def launch_app(self, name: str) -> dict:
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "cmd", "/c", "start", "", name,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            elif sys.platform == "darwin":
                proc = await asyncio.create_subprocess_exec(
                    "open", "-a", name,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    name,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            await proc.wait()
            return {"success": proc.returncode == 0, "app": name}
        except Exception as e:
            logger.error(f"Failed to launch {name}: {e}")
            return {"success": False, "error": str(e)}

    async def close_app(self, name: str) -> dict:
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "taskkill", "/IM", name, "/F",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    "pkill", "-f", name,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            await proc.wait()
            return {"success": proc.returncode == 0, "app": name}
        except Exception as e:
            logger.error(f"Failed to close {name}: {e}")
            return {"success": False, "error": str(e)}

    async def system_command(self, command: str) -> dict:
        allowed, reason = security_manager.validate_command(command)
        if not allowed:
            return {"success": False, "error": reason}

        if not security_manager.require(Permission.EXECUTE_COMMANDS):
            return {"success": False, "error": "Command execution not permitted"}

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


automation_service = DesktopAutomationService()
