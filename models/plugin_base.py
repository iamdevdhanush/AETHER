"""
AETHER Plugin Base
All plugins must inherit from PluginBase and implement its interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    """
    Abstract base class for all AETHER plugins.

    Every plugin must implement:
        initialize()  - Called once on load
        execute()     - Main plugin logic
        shutdown()    - Called on unload
        metadata()    - Plugin info dict
        settings()    - Plugin configuration schema
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Called once when the plugin is loaded.
        Set up resources, connections, state here.
        """

    @abstractmethod
    async def execute(self, payload: dict) -> Any:
        """
        Main plugin execution.

        Args:
            payload: dict with at minimum {"input": str}
                     May contain additional plugin-specific keys.

        Returns:
            Any serializable result. Will be converted to string for QML.
        """

    @abstractmethod
    def shutdown(self) -> None:
        """
        Called when the plugin is unloaded or AETHER exits.
        Clean up resources here.
        """

    @abstractmethod
    def metadata(self) -> dict:
        """
        Return plugin metadata.

        Required keys:
            name        (str)  - Unique plugin identifier
            description (str)  - Human-readable description
            version     (str)  - Semantic version
            icon        (str)  - Emoji or icon identifier
            category    (str)  - "system" | "dev" | "web" | "ai" | "general"

        Optional keys:
            author      (str)
            homepage    (str)
            requires    (list) - List of other plugin names this depends on
        """

    def settings(self) -> dict:
        """
        Return plugin settings schema.
        Override in subclasses to expose configurable options.

        Returns dict of {key: {"type": ..., "default": ..., "description": ...}}
        """
        return {}

    def get_setting(self, key: str, default=None):
        """
        Retrieve a setting value.
        Plugins can override to use database or config file storage.
        """
        schema = self.settings()
        if key in schema:
            return schema[key].get("default", default)
        return default
