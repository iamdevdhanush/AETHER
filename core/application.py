"""
AETHER Core Application v2
Orchestrates startup, initialization, and teardown.
Creates the full Agent Runtime dependency graph and wires it into QML.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread
from PySide6.QtQml import QQmlApplicationEngine

from ui.splash import SplashScreen
from core.initializer import SystemInitializer
from core.bridge import QMLBridge
from core.agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


class AetherApplication(QObject):

    initialization_complete = Signal()
    initialization_failed = Signal(str)

    def __init__(self, app: QApplication, project_root: Path):
        super().__init__()
        self.app = app
        self.project_root = project_root
        self.splash: Optional[SplashScreen] = None
        self.engine: Optional[QQmlApplicationEngine] = None
        self.bridge: Optional[QMLBridge] = None
        self.agent_runtime: Optional[AgentRuntime] = None

        # Core services
        self.db = None
        self.ollama = None
        self.plugin_manager = None
        self.conversation_service = None
        self.memory_service = None
        self.system_monitor = None
        self.tool_registry = None
        self.intent_engine = None
        self.planner = None
        self.observation_engine = None
        self.reflection_engine = None
        self.permission_manager = None
        self.reasoning_engine = None

        self._init_thread: Optional[QThread] = None

    def launch(self):
        self.splash = SplashScreen(self.project_root)
        self.splash.show()
        QTimer.singleShot(200, self._begin_initialization)

    def _begin_initialization(self):
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
        logger.info("All services initialized")

        self.db = services["db"]
        self.ollama = services["ollama"]
        self.plugin_manager = services["plugin_manager"]
        self.conversation_service = services["conversation_service"]
        self.memory_service = services["memory_service"]
        self.system_monitor = services["system_monitor"]
        self.tool_registry = services["tool_registry"]
        self.intent_engine = services["intent_engine"]
        self.planner = services["planner"]
        self.observation_engine = services["observation_engine"]
        self.reflection_engine = services["reflection_engine"]
        self.permission_manager = services["permission_manager"]
        self.reasoning_engine = services["reasoning_engine"]

        QTimer.singleShot(600, self._launch_workspace)

    @Slot(str)
    def _on_initialization_error(self, error: str):
        logger.error("Initialization failed: %s", error)
        if self.splash:
            self.splash.set_status(f"Error: {error}")

    def _launch_workspace(self):
        if self.splash:
            self.splash.close()
            self.splash = None
        self._setup_qml_engine()

    def _setup_qml_engine(self):
        self.engine = QQmlApplicationEngine()

        self.bridge = QMLBridge(
            db=self.db, ollama=self.ollama,
            plugin_manager=self.plugin_manager,
            conversation_service=self.conversation_service,
            memory_service=self.memory_service,
            system_monitor=self.system_monitor,
            project_root=self.project_root,
            agent_runtime=None,
        )

        self.agent_runtime = AgentRuntime(
            tool_registry=self.tool_registry,
            intent_engine=self.intent_engine,
            planner=self.planner,
            reasoning_engine=self.reasoning_engine,
            observation_engine=self.observation_engine,
            reflection_engine=self.reflection_engine,
            permission_manager=self.permission_manager,
            ollama=self.ollama,
            memory_service=self.memory_service,
            conversation_service=self.conversation_service,
            bridge=self.bridge,
        )
        self.bridge.agent_runtime = self.agent_runtime

        self.engine.rootContext().setContextProperty("bridge", self.bridge)
        self.engine.rootContext().setContextProperty(
            "projectRoot", str(self.project_root),
        )

        main_qml = self.project_root / "ui" / "qml" / "Main.qml"
        self.engine.load(str(main_qml))

        if not self.engine.rootObjects():
            logger.error("Failed to load Main.qml")
            self.app.quit()
            return

        logger.info("AETHER workspace launched")

    def cleanup(self):
        logger.info("AETHER shutting down...")
        if self.bridge:
            self.bridge.cleanup()
        if self.plugin_manager:
            self.plugin_manager.shutdown_all()
        if self.system_monitor:
            self.system_monitor.stop()
        if self.ollama:
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.ollama.close())
                loop.close()
            except Exception:
                pass
        if self.db:
            self.db.close()
