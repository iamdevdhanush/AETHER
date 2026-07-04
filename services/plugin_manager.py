"""
AETHER Plugin Manager v2
Discovers plugins and ToolBase implementations.
Each discovered plugin is registered as a Tool in the ToolRegistry.
"""

import logging
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional

from models.plugin_base import PluginBase
from models.tool_base import ToolBase
from core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class PluginManager:

    PLUGIN_STUBS = {
        "terminal":   {"description": "Execute shell commands",           "icon": "⌨️", "category": "system"},
        "filesystem": {"description": "Browse and manage files",          "icon": "📁", "category": "system"},
        "browser":    {"description": "Open URLs or search the web",      "icon": "🌐", "category": "web"},
        "executor":   {"description": "Execute Python code snippets",     "icon": "▶️", "category": "dev"},
        "vscode":     {"description": "Open files in Visual Studio Code", "icon": "💻", "category": "dev"},
        "sysmon":     {"description": "System CPU, RAM, disk stats",      "icon": "📊", "category": "system"},
        "memory":     {"description": "Memory management interface",      "icon": "🧠", "category": "ai"},
        "voice":      {"description": "Speech-to-text and text-to-speech","icon": "🎙️", "category": "ai"},
        "vision":     {"description": "Camera capture and AI analysis",   "icon": "👁️", "category": "ai"},
        "docker":     {"description": "Manage Docker containers/images",  "icon": "🐳", "category": "dev"},
        "git":        {"description": "Git commit, push, pull, status",   "icon": "🔀", "category": "dev"},
        "system":     {"description": "Shutdown, restart, screenshot",    "icon": "⚙️", "category": "system"},
    }

    def __init__(self, plugins_dir: Path, tool_registry: ToolRegistry):
        self.plugins_dir = plugins_dir
        self.tool_registry = tool_registry
        self._paths: dict[str, Path] = {}
        self._instances: dict[str, ToolBase] = {}
        self._loaded: set[str] = set()

    def discover_and_load(self):
        if not self.plugins_dir.exists():
            logger.warning("Plugins directory not found: %s", self.plugins_dir)
            return

        for plugin_dir in sorted(self.plugins_dir.iterdir()):
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue
            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue
            self._paths[plugin_dir.name] = plugin_file

        logger.info("Discovered %d plugin paths", len(self._paths))

        for name in list(self._paths.keys()):
            self._load_and_register(name)

        logger.info("Loaded and registered %d tools", len(self._instances))

    def _load_and_register(self, name: str) -> Optional[ToolBase]:
        plugin_file = self._paths.get(name)
        if not plugin_file:
            return None

        try:
            plugin_dir = plugin_file.parent
            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))

            module_name = f"plugins.{name}.plugin"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                logger.error("Cannot create spec for '%s'", name)
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            instance = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ToolBase) and attr is not ToolBase:
                    instance = attr()
                    break

            if instance is None:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                        instance = attr()
                        logger.info("Loaded '%s' as legacy PluginBase (wrapping as tool)", name)
                        break

            if instance is None:
                logger.warning("No ToolBase or PluginBase subclass found in %s", plugin_file)
                return None

            if isinstance(instance, PluginBase):
                from core.tool_registry import LegacyPluginAdapter
                instance = LegacyPluginAdapter(instance)

            try:
                instance.initialize()
            except Exception as e:
                logger.debug("initialize() not required for tool '%s': %s", name, e)

            self._instances[name] = instance
            self.tool_registry.register(instance)
            self._loaded.add(name)
            logger.info("Registered tool: %s — %s", name, instance.description()[:60])
            return instance

        except Exception as e:
            logger.error("Failed to load '%s': %s", name, e, exc_info=True)
            return None

    def get_plugin(self, name: str) -> Optional[ToolBase]:
        return self._instances.get(name)

    def get_plugin_list(self) -> list[dict]:
        result = []
        for name in self._paths:
            if name in self._instances:
                tool = self._instances[name]
                result.append({
                    "name": name,
                    "description": tool.description(),
                    "version": "1.0.0",
                    "icon": self.PLUGIN_STUBS.get(name, {}).get("icon", "🔌"),
                    "category": self.PLUGIN_STUBS.get(name, {}).get("category", "general"),
                    "enabled": True,
                })
            else:
                stub = self.PLUGIN_STUBS.get(name, {})
                result.append({
                    "name": name, "description": stub.get("description", ""),
                    "version": "1.0.0", "icon": stub.get("icon", "🔌"),
                    "category": stub.get("category", "general"), "enabled": False,
                })
        return result

    def shutdown_all(self):
        for name, tool in self._instances.items():
            try:
                tool.shutdown()
            except Exception as e:
                logger.error("Error shutting down %s: %s", name, e)
        self.tool_registry.shutdown_all()

    def reload_plugin(self, name: str) -> bool:
        if name in self._instances:
            try:
                self._instances[name].shutdown()
            except Exception:
                pass
            del self._instances[name]
            self._loaded.discard(name)
        return self._load_and_register(name) is not None

    def list_names(self) -> list[str]:
        return list(self._paths.keys())

    @property
    def loaded_count(self) -> int:
        return len(self._loaded)
