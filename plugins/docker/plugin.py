"""
AETHER Docker Plugin
Manage Docker containers and images via the Docker CLI.
"""

import asyncio
import logging
import sys
import json
from shutil import which

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class DockerPlugin(PluginBase):

    def initialize(self):
        self._docker_path = which("docker") or self._find_docker()
        if self._docker_path:
            logger.info("Docker found at: %s", self._docker_path)
        else:
            logger.warning("Docker CLI not found")

    def _find_docker(self):
        if sys.platform == "win32":
            candidates = [
                "C:/Program Files/Docker/Docker/resources/bin/docker.exe",
                "C:/Program Files/Docker/Docker/resources/bin/com.docker.cli.exe",
            ]
            for p in candidates:
                from pathlib import Path
                if Path(p).exists():
                    return p
        return None

    async def execute(self, payload: dict) -> str:
        if not self._docker_path:
            return (
                "Docker CLI not found. Install Docker Desktop from "
                "https://www.docker.com/products/docker-desktop/"
            )

        input_str = payload.get("input", "").strip().lower()

        if not input_str or input_str in ("ps", "list", "containers"):
            return await self._run_docker("ps -a")
        if input_str.startswith("ps "):
            return await self._run_docker(input_str)
        if input_str in ("images", "image"):
            return await self._run_docker("images")
        if input_str.startswith("pull "):
            return await self._run_docker(input_str)
        if input_str.startswith("run "):
            return await self._run_docker(input_str)
        if input_str.startswith("stop "):
            return await self._run_docker(input_str)
        if input_str.startswith("start "):
            return await self._run_docker(input_str)
        if input_str.startswith("rm "):
            return await self._run_docker(input_str)
        if input_str.startswith("rmi "):
            return await self._run_docker(input_str)
        if input_str == "info":
            return await self._run_docker("info")
        if input_str == "version":
            return await self._run_docker("version")

        return await self._run_docker(input_str)

    async def _run_docker(self, args: str) -> str:
        cmd = f"{self._docker_path} {args}"
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True,
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    executable="/bin/bash",
                )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=30.0,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return "Docker command timed out after 30 seconds."

            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(
                    f"[stderr]\n{stderr.decode('utf-8', errors='replace')}",
                )

            result = "\n".join(output_parts).strip()
            return result or f"(exit code: {proc.returncode})"

        except FileNotFoundError:
            return "Docker command not found."
        except Exception as e:
            logger.error("Docker error: %s", e, exc_info=True)
            return f"Docker error: {e}"

    def shutdown(self):
        logger.info("Docker plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "docker",
            "description": "Manage Docker containers and images via CLI",
            "version": "1.0.0",
            "icon": "🐳",
            "category": "dev",
        }
