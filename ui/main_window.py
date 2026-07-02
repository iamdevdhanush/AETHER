from __future__ import annotations
import sys
from pathlib import Path
from typing import Any
from PySide6.QtCore import QUrl, QSize
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from ui.bridge import ApplicationBridge
from ui.state import AppState, BridgeState


class AetherWindow:
    def __init__(
        self,
        app_state: AppState,
        bridge_state: BridgeState,
        plugin_manager: Any = None,
        conversation_manager: Any = None,
    ) -> None:
        self._app_state = app_state
        self._bridge_state = bridge_state
        self._plugin_manager = plugin_manager
        self._conversation_manager = conversation_manager
        self._engine: QQmlApplicationEngine | None = None
        self._bridge: ApplicationBridge | None = None
        self._window: QQuickWindow | None = None

    def setup(self) -> None:
        QQuickWindow.setSceneGraphBackend("opengl")

        self._engine = QQmlApplicationEngine()
        self._bridge = ApplicationBridge(
            self._app_state,
            self._bridge_state,
            plugin_manager=self._plugin_manager,
            conversation_manager=self._conversation_manager,
        )
        self._engine.rootContext().setContextProperty("bridge", self._bridge)

        self._engine.warnings.connect(self._on_qml_warning)

        qml_path = Path(__file__).parent / "qml" / "Main.qml"
        print(f"[AETHER] Loading QML: {qml_path}")
        self._engine.load(QUrl.fromLocalFile(str(qml_path)))

        if not self._engine.rootObjects():
            raise RuntimeError("Failed to load QML (see warnings above)")

        self._window = self._engine.rootObjects()[0]
        self._setup_window()

    def _on_qml_warning(self, warnings) -> None:
        for w in warnings:
            print(f"[AETHER] QML Warning: {w.toString()}")

    def _setup_window(self) -> None:
        if not self._window:
            return
        self._window.setTitle("AETHER")
        self._window.setMinimumSize(QSize(900, 600))
        self._window.resize(1280, 800)
        self._window.show()

    def get_bridge(self) -> ApplicationBridge:
        if not self._bridge:
            raise RuntimeError("Bridge not initialized")
        return self._bridge

    def get_engine(self) -> QQmlApplicationEngine:
        if not self._engine:
            raise RuntimeError("Engine not initialized")
        return self._engine
