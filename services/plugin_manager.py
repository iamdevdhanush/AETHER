"""
AETHER Plugin Manager
Lazy-loading plugin registry.
Discovers plugins at startup but only imports modules on first use.
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
    Lazy plugin registry.
    Discovers plugin paths at startup without importing modules.
    Import + instantiation happens only when get_plugin() is called.
    """

    # Static metadata for quick listing without import
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

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._registry: dict[str, PluginBase] = {}
        self._paths: dict[str, Path] = {}
        self._loaded: set[str] = set()

    def discover_and_load(self):
        """
        Discover all valid plugin directories and register paths.
        Does NOT import plugin modules — that happens on first use.
        """
        if not self.plugins_dir.exists():
            logger.warning("Plugins directory not found: %s", self.plugins_dir)
            return

        for plugin_dir in sorted(self.plugins_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            if plugin_dir.name.startswith("_"):
                continue

            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue

            self._paths[plugin_dir.name] = plugin_file

        logger.info(
            "Discovered %d plugins (none imported yet): %s",
            len(self._paths), list(self._paths.keys()),
        )

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin instance, loading it on first access."""
        if name in self._registry:
            return self._registry[name]

        plugin_file = self._paths.get(name)
        if not plugin_file:
            logger.warning("Plugin '%s' not found in discovered paths", name)
            return None

        return self._do_load(name, plugin_file)

    def _do_load(self, name: str, plugin_file: Path) -> Optional[PluginBase]:
        """Import and instantiate a single plugin."""
        try:
            plugin_dir = plugin_file.parent

            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))

            module_name = f"plugins.{name}.plugin"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                logger.error("Cannot create spec for plugin '%s'", name)
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

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
                logger.warning("No PluginBase subclass found in %s", plugin_file)
                return None

            instance: PluginBase = plugin_class()
            meta = instance.metadata()
            registered_name = meta.get("name", name)
            instance.initialize()
            self._registry[registered_name] = instance
            self._loaded.add(registered_name)
            logger.info(
                "Loaded plugin: %s v%s (%s)",
                registered_name, meta.get("version", "?"), meta.get("category", "?"),
            )
            return instance

        except Exception as e:
            logger.error("Failed to load plugin '%s': %s", name, e, exc_info=True)
            return None

    def get_plugin_list(self) -> list[dict]:
        """
        Return plugin metadata for QML listing.
        Uses static stubs — no module imports required.
        For plugins that have been loaded, returns real metadata.
        """
        result = []
        for name in self._paths:
            if name in self._registry:
                try:
                    meta = self._registry[name].metadata()
                    result.append({
                        "name": meta.get("name", name),
                        "description": meta.get("description", ""),
                        "version": meta.get("version", "1.0.0"),
                        "icon": meta.get("icon", "🔌"),
                        "category": meta.get("category", "general"),
                        "enabled": True,
                    })
                    continue
                except Exception:
                    pass

            stub = self.PLUGIN_STUBS.get(name, {})
            result.append({
                "name": name,
                "description": stub.get("description", ""),
                "version": "1.0.0",
                "icon": stub.get("icon", "🔌"),
                "category": stub.get("category", "general"),
                "enabled": True,
            })

        return result

    def shutdown_all(self):
        """Gracefully shut down all loaded plugins."""
        for name, plugin in self._registry.items():
            try:
                plugin.shutdown()
                logger.debug("Shut down plugin: %s", name)
            except Exception as e:
                logger.error("Error shutting down plugin %s: %s", name, e)

    def reload_plugin(self, name: str) -> bool:
        """Reload a single plugin by name (only if already loaded)."""
        if name not in self._registry:
            return self._do_load(name, self._paths.get(name)) is not None

        plugin = self._registry[name]
        try:
            plugin.shutdown()
        except Exception:
            pass

        del self._registry[name]
        self._loaded.discard(name)

        plugin_file = self._paths.get(name)
        if plugin_file and plugin_file.exists():
            return self._do_load(name, plugin_file) is not None
        return False

    def list_names(self) -> list[str]:
        """Return all discovered plugin names (not necessarily loaded)."""
        return list(self._paths.keys())

    @property
    def loaded_count(self) -> int:
        return len(self._loaded)
