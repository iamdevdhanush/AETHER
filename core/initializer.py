"""
AETHER System Initializer v2
Sequential initialization of all subsystems.
Creates the complete agent runtime dependency graph.
"""

import logging
import asyncio
from pathlib import Path

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SystemInitializer(QThread):

    status_update = Signal(str)
    initialization_done = Signal(object)
    initialization_error = Signal(str)

    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root

    def run(self):
        try:
            services = {}

            # Step 1: Database
            self.status_update.emit("Initializing database...")
            from database.db_manager import DatabaseManager
            db = DatabaseManager(self.project_root / "data" / "aether.db")
            db.initialize()
            services["db"] = db

            # Step 2: Ollama
            self.status_update.emit("Connecting to Ollama...")
            from services.ollama_service import OllamaService
            ollama = OllamaService()
            services["ollama"] = ollama

            # Step 3: Memory (long-term + short-term + working)
            self.status_update.emit("Loading memory engine...")
            from services.memory_service import MemoryService
            memory = MemoryService(db, ollama)
            services["memory_service"] = memory

            # Step 4: Conversation
            self.status_update.emit("Initializing conversation engine...")
            from services.conversation_service import ConversationService
            conversation = ConversationService(db, ollama, memory)
            services["conversation_service"] = conversation

            # Step 5: Tool Registry
            self.status_update.emit("Creating tool registry...")
            from core.tool_registry import ToolRegistry
            tool_registry = ToolRegistry()
            services["tool_registry"] = tool_registry

            # Step 6: Plugins -> register as tools
            self.status_update.emit("Loading and registering tools...")
            from services.plugin_manager import PluginManager
            plugin_manager = PluginManager(self.project_root / "plugins", tool_registry)
            plugin_manager.discover_and_load()
            services["plugin_manager"] = plugin_manager

            # Step 7: Core engine components
            self.status_update.emit("Initializing agent engines...")
            from core.intent_router import IntentRouter
            from core.planner import Planner
            from core.observation_engine import ObservationEngine
            from core.reflection_engine import ReflectionEngine
            from core.permission_manager import PermissionManager
            from core.reasoning_engine import ReasoningEngine

            intent_router = IntentRouter(tool_registry, ollama)
            planner = Planner(tool_registry, ollama)
            observation_engine = ObservationEngine()
            reflection_engine = ReflectionEngine(ollama)
            permission_manager = PermissionManager()

            reasoning_engine = ReasoningEngine(
                tool_registry=tool_registry,
                observation_engine=observation_engine,
                reflection_engine=reflection_engine,
                permission_manager=permission_manager,
                ollama=ollama,
            )

            services["intent_router"] = intent_router
            services["planner"] = planner
            services["observation_engine"] = observation_engine
            services["reflection_engine"] = reflection_engine
            services["permission_manager"] = permission_manager
            services["reasoning_engine"] = reasoning_engine

            # Step 8: System Monitor
            self.status_update.emit("Starting system monitor...")
            from services.system_monitor import SystemMonitorService
            sysmon = SystemMonitorService()
            sysmon.start()
            services["system_monitor"] = sysmon

            self.status_update.emit("Ready.")
            self.initialization_done.emit(services)

        except Exception as e:
            logger.exception("Initialization failed")
            self.initialization_error.emit(str(e))
