from dataclasses import dataclass, field
from typing import Any, Callable
from loguru import logger


@dataclass
class Plugin:
    id: str
    name: str
    description: str
    version: str
    enabled: bool = True
    handlers: dict[str, Callable] = field(default_factory=dict)


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        self.plugins[plugin.id] = plugin
        logger.info(f"Plugin registered: {plugin.name} v{plugin.version}")

    def unregister(self, plugin_id: str):
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            logger.info(f"Plugin unregistered: {plugin_id}")

    def enable(self, plugin_id: str):
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = True
            logger.info(f"Plugin enabled: {plugin_id}")

    def disable(self, plugin_id: str):
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = False
            logger.info(f"Plugin disabled: {plugin_id}")

    def get_enabled_plugins(self) -> list[Plugin]:
        return [p for p in self.plugins.values() if p.enabled]

    def get_all_plugins(self) -> list[dict]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "enabled": p.enabled,
            }
            for p in self.plugins.values()
        ]


plugin_manager = PluginManager()


# Register built-in plugins
plugin_manager.register(Plugin(
    id="conversation",
    name="Conversation",
    description="Natural conversation with LLM",
    version="1.0.0",
))
plugin_manager.register(Plugin(
    id="voice",
    name="Voice",
    description="Speech-to-text and text-to-speech",
    version="1.0.0",
))
plugin_manager.register(Plugin(
    id="memory",
    name="Memory",
    description="Conversation history and vector search",
    version="1.0.0",
))
plugin_manager.register(Plugin(
    id="automation",
    name="Desktop Automation",
    description="Launch, close, and manage applications",
    version="1.0.0",
))
plugin_manager.register(Plugin(
    id="files",
    name="File System",
    description="Search, read, and manage files",
    version="1.0.0",
))
plugin_manager.register(Plugin(
    id="code",
    name="Developer Mode",
    description="Code understanding and generation",
    version="1.0.0",
    enabled=False,
))
plugin_manager.register(Plugin(
    id="vision",
    name="Vision",
    description="Screenshot understanding and OCR",
    version="1.0.0",
    enabled=False,
))
plugin_manager.register(Plugin(
    id="system",
    name="System Monitor",
    description="CPU, RAM, GPU, disk monitoring",
    version="1.0.0",
))
