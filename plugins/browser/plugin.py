"""
AETHER Browser Plugin
Open URLs in the system default browser.
"""

import logging
import webbrowser
import re
from urllib.parse import quote_plus

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(
    r'^(https?://|www\.)\S+', re.IGNORECASE
)


class BrowserPlugin(PluginBase):
    """
    Open URLs or search queries in the system default browser.
    Automatically prepends https:// if missing.
    Converts plain text to a Google search if not a URL.
    """

    def initialize(self):
        logger.info("Browser plugin initialized")

    async def execute(self, payload: dict) -> str:
        query = payload.get("input", "").strip()

        if not query:
            return "No URL or search query provided."

        url = self._resolve_url(query)

        try:
            opened = webbrowser.open(url, new=2, autoraise=True)
            if opened:
                return f"Opened in browser: {url}"
            else:
                return f"Failed to open browser. URL: {url}"
        except Exception as e:
            logger.error(f"Browser launch error: {e}")
            return f"Error opening browser: {e}"

    def _resolve_url(self, query: str) -> str:
        """Convert query to a URL."""
        # Already a URL
        if URL_PATTERN.match(query):
            if not query.startswith("http"):
                return "https://" + query
            return query

        # Domain-like (contains a dot, no spaces)
        if "." in query and " " not in query:
            return "https://" + query

        # Default: Google search
        return f"https://www.google.com/search?q={quote_plus(query)}"

    def shutdown(self):
        logger.info("Browser plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "browser",
            "description": "Open URLs or search the web in your default browser",
            "version": "1.0.0",
            "icon": "🌐",
            "category": "web",
        }
