"""
AETHER Core Application
Orchestrates startup, initialization, and teardown.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType

from ui.splash import SplashScreen
from core.initializer import SystemInitializer
from core.bridge import QMLBridge
from database.db_manager import DatabaseManager
from services.ollama_service import OllamaService
from services.plugin_manager import PluginManager
from services.conversation_service import ConversationService
from services.memory_service import MemoryService
from services.system_monitor import SystemMonitorService

logger = logging.getLogger(__name__)


class AetherApplication(QObject):
    """
    Top-level application coordinator.
    Manages splash → init → workspace lifecycle.
    """

    initialization_complete = Signal()
    initialization_failed = Signal(str)

    def __init__(self, app: QApplication, project_root: Path):
        super().__init__()
        self.app = app
        self.project_root = project_root
        self.splash: Optional[SplashScreen] = None
        self.engine: Optional[QQmlApplicationEngine] = None
        self.bridge: Optional[QMLBridge] = None

        # Core services
        self.db: Optional[DatabaseManager] = None
        self.ollama: Optional[OllamaService] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.conversation_service: Optional[ConversationService] = None
        self.memory_service: Optional[MemoryService] = None
        self.system_monitor: Optional[SystemMonitorService] = None

        # Async event loop thread
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._init_thread: Optional[QThread] = None

    def launch(self):
        """Show splash and begin initialization."""
        self.splash = SplashScreen(self.project_root)
        self.splash.show()

        # Delay to let splash render
        QTimer.singleShot(200, self._begin_initialization)

    def _begin_initialization(self):
        """Run initialization in a worker thread to keep UI responsive."""
        self.initializer = SystemInitializer(self.project_root)
        self.initializer.status_update.connect(self._on_status_update)
        self.initializer.initialization_done.connect(self._on_initialization_done)
        self.initializer.initialization_error.connect(self._on_initialization_error)
        self.initializer.start()

    @Slot(str)
    def _on_status_update(self, message: str):
        if self.splash:
            self.splash.set_status(message)

    @Slot(object)
    def _on_initialization_done(self, services: dict):
        """Called when all services are ready."""
        logger.info("All services initialized")

        self.db = services["db"]
        self.ollama = services["ollama"]
        self.plugin_manager = services["plugin_manager"]
        self.conversation_service = services["conversation_service"]
        self.memory_service = services["memory_service"]
        self.system_monitor = services["system_monitor"]

        # Small pause so user sees "Ready"
        QTimer.singleShot(600, self._launch_workspace)

    @Slot(str)
    def _on_initialization_error(self, error: str):
        logger.error(f"Initialization failed: {error}")
        if self.splash:
            self.splash.set_status(f"Error: {error}")

    def _launch_workspace(self):
        """Tear down splash and open the main QML workspace."""
        if self.splash:
            self.splash.close()
            self.splash = None

        self._setup_qml_engine()

    def _setup_qml_engine(self):
        """Configure QML engine, register bridge, load main QML."""
        from core.bridge import QMLBridge

        self.engine = QQmlApplicationEngine()

        # Create bridge connecting QML ↔ Python services
        self.bridge = QMLBridge(
            db=self.db,
            ollama=self.ollama,
            plugin_manager=self.plugin_manager,
            conversation_service=self.conversation_service,
            memory_service=self.memory_service,
            system_monitor=self.system_monitor,
            project_root=self.project_root,
        )

        # Expose bridge to QML
        self.engine.rootContext().setContextProperty("bridge", self.bridge)
        self.engine.rootContext().setContextProperty(
            "projectRoot", str(self.project_root)
        )

        # Load main QML file
        main_qml = self.project_root / "ui" / "qml" / "Main.qml"
        self.engine.load(str(main_qml))

        if not self.engine.rootObjects():
            logger.error("Failed to load Main.qml")
            self.app.quit()
            return

        logger.info("AETHER workspace launched")

    def cleanup(self):
        """Graceful shutdown."""
        logger.info("AETHER shutting down...")
        if self.plugin_manager:
            self.plugin_manager.shutdown_all()
        if self.system_monitor:
            self.system_monitor.stop()
        if self.db:
            self.db.close()
