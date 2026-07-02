from __future__ import annotations
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any
from models import PluginInfo


class BasePlugin:
    id: str = ""
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    enabled: bool = True

    async def initialize(self) -> None:
        pass

    async def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def shutdown(self) -> None:
        pass

    def metadata(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description, "version": self.version}

    def settings(self) -> dict:
        return {}


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._infos: dict[str, PluginInfo] = {}

    def register(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.id] = plugin
        self._infos[plugin.id] = PluginInfo(
            id=plugin.id,
            name=plugin.name,
            description=plugin.description,
            version=plugin.version,
            enabled=plugin.enabled,
            plugin_type="system",
        )

    def get(self, plugin_id: str) -> BasePlugin | None:
        return self._plugins.get(plugin_id)

    def get_info(self, plugin_id: str) -> PluginInfo | None:
        return self._infos.get(plugin_id)

    def get_all_infos(self) -> list[dict]:
        return [
            {
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "enabled": info.enabled,
                "plugin_type": info.plugin_type,
            }
            for info in self._infos.values()
        ]

    def enable(self, plugin_id: str) -> bool:
        if plugin_id in self._infos:
            self._infos[plugin_id].enabled = True
            return True
        return False

    def disable(self, plugin_id: str) -> bool:
        if plugin_id in self._infos:
            self._infos[plugin_id].enabled = False
            return True
        return False

    async def initialize_all(self) -> None:
        for plugin_id, plugin in self._plugins.items():
            if self._infos[plugin_id].enabled:
                await plugin.initialize()

    async def shutdown_all(self) -> None:
        for plugin in self._plugins.values():
            await plugin.shutdown()

    def load_from_module(self, module_name: str) -> None:
        module = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
            ):
                instance = obj()
                self.register(instance)


plugin_manager = PluginManager()
