"""
AETHER Docker Tool
Manage Docker containers and images via the Docker CLI.
"""

import asyncio
import logging
import sys
import time
from shutil import which

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class DockerPlugin(ToolBase):

    def name(self) -> str:
        return "docker"

    def description(self) -> str:
        return "Manage Docker containers and images: ps, images, pull, run, stop, start, rm, logs"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Docker command (e.g. ps, images, pull nginx, run ...)"},
            },
            "required": ["input"],
        }

    def initialize(self):
        self._docker_path = which("docker") or self._find_docker()
        if self._docker_path:
            logger.info("Docker found at: %s", self._docker_path)
        else:
            logger.warning("Docker CLI not found")

    def _find_docker(self):
        if sys.platform == "win32":
            from pathlib import Path
            candidates = ["C:/Program Files/Docker/Docker/resources/bin/docker.exe",
                          "C:/Program Files/Docker/Docker/resources/bin/com.docker.cli.exe"]
            for p in candidates:
                if Path(p).exists():
                    return p
        return None

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        if not self._docker_path:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr="Docker CLI not found. Install Docker Desktop.", exit_code=1, success=False, execution_time_ms=elapsed)

        input_str = params.get("input", "").strip()
        if not input_str or input_str in ("ps", "list", "containers"):
            input_str = "ps -a"
        elif input_str in ("images", "image"):
            input_str = "images"
        elif input_str.startswith("logs "):
            input_str = input_str

        return await self._run_docker(input_str, start)

    async def _run_docker(self, args: str, start: float) -> ToolObservation:
        cmd = f"{self._docker_path} {args}"
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True)
            else:
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, executable="/bin/bash")
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                proc.kill()
                elapsed = (time.time() - start) * 1000
                return ToolObservation(stdout="", stderr="Docker command timed out.", exit_code=-1, success=False, execution_time_ms=elapsed)

            elapsed = (time.time() - start) * 1000
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            return ToolObservation(stdout=stdout_str, stderr=stderr_str, exit_code=proc.returncode or 0, success=proc.returncode == 0, execution_time_ms=elapsed)
        except FileNotFoundError:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr="Docker command not found.", exit_code=1, success=False, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Docker error: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        logger.info("Docker tool shut down")
