"""
AETHER System Initializer
Runs all startup tasks in a QThread to keep the splash screen responsive.
"""

import logging
import asyncio
from pathlib import Path

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SystemInitializer(QThread):
    """
    Sequential initialization of all AETHER subsystems.
    Emits status_update for each step, then initialization_done with service dict.
    """

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

            # Step 3: Memory
            self.status_update.emit("Loading memory...")
            from services.memory_service import MemoryService
            memory = MemoryService(db)
            services["memory_service"] = memory

            # Step 4: Conversation
            self.status_update.emit("Initializing conversation engine...")
            from services.conversation_service import ConversationService
            conversation = ConversationService(db, ollama, memory)
            services["conversation_service"] = conversation

            # Step 5: Plugins
            self.status_update.emit("Loading plugins...")
            from services.plugin_manager import PluginManager
            plugin_manager = PluginManager(self.project_root / "plugins")
            plugin_manager.discover_and_load()
            services["plugin_manager"] = plugin_manager

            # Step 6: System Monitor
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
