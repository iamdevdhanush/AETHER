"""
AETHER Browser Tool
Open URLs in the system default browser or perform web searches.
"""

import logging
import webbrowser
import re
import time
from urllib.parse import quote_plus

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'^(https?://|www\.)\S+', re.IGNORECASE)


class BrowserPlugin(ToolBase):

    def name(self) -> str:
        return "browser"

    def description(self) -> str:
        return "Open URLs or search the web in your default browser"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "URL or search query"},
                "action": {"type": "string", "enum": ["open", "search"]},
            },
            "required": ["input"],
        }

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        query = params.get("input", "").strip()
        if not query:
            return ToolObservation(stdout="", stderr="No URL or search query provided.", exit_code=1, success=False)

        url = self._resolve_url(query)
        try:
            opened = webbrowser.open(url, new=2, autoraise=True)
            elapsed = (time.time() - start) * 1000
            if opened:
                return ToolObservation(stdout=f"Opened in browser: {url}", exit_code=0, success=True, execution_time_ms=elapsed)
            return ToolObservation(stdout="", stderr=f"Failed to open browser. URL: {url}", exit_code=1, success=False, execution_time_ms=elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ToolObservation(stdout="", stderr=f"Error opening browser: {e}", exit_code=1, success=False, execution_time_ms=elapsed)

    def _resolve_url(self, query: str) -> str:
        if URL_PATTERN.match(query):
            if not query.startswith("http"):
                return "https://" + query
            return query
        if "." in query and " " not in query:
            return "https://" + query
        return f"https://www.google.com/search?q={quote_plus(query)}"

    def shutdown(self):
        logger.info("Browser tool shut down")
