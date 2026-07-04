"""
AETHER Executor Tool
Execute Python code snippets safely.
"""

import asyncio
import logging
import sys
import io
import traceback
import time
from contextlib import redirect_stdout, redirect_stderr

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class ExecutorPlugin(ToolBase):

    def name(self) -> str:
        return "executor"

    def description(self) -> str:
        return "Execute Python code snippets and return output"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["input"],
        }

    def initialize(self):
        self._exec_globals = {"__builtins__": __builtins__, "__name__": "__aether_exec__"}
        logger.info("Executor plugin initialized")

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        code = params.get("input", "").strip()
        if not code:
            return ToolObservation(stdout="", stderr="No code to execute.", exit_code=1, success=False)

        if code.startswith("```"):
            lines = code.split("\n")
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
                        try:
                            compiled = compile(code, "<aether>", "eval")
                            result = eval(compiled, exec_globals, exec_locals)
                            if result is not None:
                                print(repr(result))
                        except SyntaxError:
                            compiled = compile(code, "<aether>", "exec")
                            exec(compiled, exec_globals, exec_locals)
                    except Exception:
                        traceback.print_exc(file=stderr_buf)

            await loop.run_in_executor(None, _exec)

            elapsed = (time.time() - start) * 1000
            stdout_out = stdout_buf.getvalue()
            stderr_out = stderr_buf.getvalue()

            if stderr_out:
                return ToolObservation(stdout=stdout_out, stderr=stderr_out, exit_code=1, success=False, execution_time_ms=elapsed)
            return ToolObservation(stdout=stdout_out or "(no output)", exit_code=0, success=True, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Execution error: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def shutdown(self):
        logger.info("Executor tool shut down")
