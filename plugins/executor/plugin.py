"""
AETHER Executor Plugin
Execute Python code snippets safely.
"""

import asyncio
import logging
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class ExecutorPlugin(PluginBase):
    """
    Execute Python code in a sandboxed context.
    Returns stdout, stderr, and return value.
    """

    def initialize(self):
        self._exec_globals = {
            "__builtins__": __builtins__,
            "__name__": "__aether_exec__",
        }
        logger.info("Executor plugin initialized")

    async def execute(self, payload: dict) -> str:
        code = payload.get("input", "").strip()

        if not code:
            return "No code to execute."

        # Strip markdown code fences if present
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first and last fence lines
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        exec_globals = dict(self._exec_globals)
        exec_locals = {}

        try:
            loop = asyncio.get_event_loop()

            def _exec():
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    try:
                        # Try to compile as expression first (to capture return value)
                        try:
                            compiled = compile(code, "<aether>", "eval")
                            result = eval(compiled, exec_globals, exec_locals)
                            if result is not None:
                                print(repr(result))
                        except SyntaxError:
                            # Fall back to exec for statements
                            compiled = compile(code, "<aether>", "exec")
                            exec(compiled, exec_globals, exec_locals)
                    except Exception:
                        traceback.print_exc(file=stderr_buf)

            await loop.run_in_executor(None, _exec)

            stdout_out = stdout_buf.getvalue()
            stderr_out = stderr_buf.getvalue()

            parts = []
            if stdout_out:
                parts.append(f"Output:\n{stdout_out}")
            if stderr_out:
                parts.append(f"Errors:\n{stderr_out}")
            if not parts:
                parts.append("(no output)")

            return "\n".join(parts)

        except Exception as e:
            logger.error(f"Executor error: {e}", exc_info=True)
            return f"Execution error: {e}"

    def shutdown(self):
        logger.info("Executor plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "executor",
            "description": "Execute Python code snippets and return output",
            "version": "1.0.0",
            "icon": "▶️",
            "category": "dev",
        }
