"""
AETHER Plugin Manager
Discovers, loads, and manages all AETHER plugins dynamically.
"""

import logging
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Dynamic plugin loader and registry.
    Scans the plugins directory for valid plugin packages.
    """

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._registry: dict[str, PluginBase] = {}

    def discover_and_load(self):
        """
        Scan plugins directory and load every valid plugin.
        A valid plugin is a directory with a plugin.py file containing
        a class inheriting from PluginBase.
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return

        for plugin_dir in sorted(self.plugins_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            if plugin_dir.name.startswith("_"):
                continue

            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue

            self._load_plugin(plugin_dir, plugin_file)

        logger.info(f"Loaded {len(self._registry)} plugins: {list(self._registry.keys())}")

    def _load_plugin(self, plugin_dir: Path, plugin_file: Path):
        """Load a single plugin from its directory."""
        plugin_name = plugin_dir.name

        try:
            # Add plugin dir to path so it can import its own modules
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))

            module_name = f"plugins.{plugin_name}.plugin"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginBase)
                    and attr is not PluginBase
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.warning(f"No PluginBase subclass found in {plugin_file}")
                return

            # Instantiate and initialize
            instance: PluginBase = plugin_class()
            meta = instance.metadata()
            registered_name = meta.get("name", plugin_name)

            instance.initialize()

            self._registry[registered_name] = instance
            logger.info(f"Loaded plugin: {registered_name} v{meta.get('version', '?')}")

        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        return self._registry.get(name)

    def get_plugin_list(self) -> list[dict]:
        """Return serializable list of plugin metadata for QML."""
        result = []
        for name, plugin in self._registry.items():
            try:
                meta = plugin.metadata()
                result.append({
                    "name": meta.get("name", name),
                    "description": meta.get("description", ""),
                    "version": meta.get("version", "1.0.0"),
                    "icon": meta.get("icon", "🔌"),
                    "category": meta.get("category", "general"),
                    "enabled": True,
                })
            except Exception as e:
                logger.error(f"Error getting metadata for plugin {name}: {e}")
        return result

    def shutdown_all(self):
        """Gracefully shut down all plugins."""
        for name, plugin in self._registry.items():
            try:
                plugin.shutdown()
                logger.debug(f"Shut down plugin: {name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {e}")

    def reload_plugin(self, name: str) -> bool:
        """Reload a single plugin by name."""
        if name not in self._registry:
            return False

        plugin = self._registry[name]
        try:
            plugin.shutdown()
        except Exception:
            pass

        del self._registry[name]

        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir.name == name:
                plugin_file = plugin_dir / "plugin.py"
                if plugin_file.exists():
                    self._load_plugin(plugin_dir, plugin_file)
                    return name in self._registry

        return False

    def list_names(self) -> list[str]:
        return list(self._registry.keys())
