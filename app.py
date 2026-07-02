#!/usr/bin/env python3

import sys
import asyncio
import threading
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from services.config import settings
from services.database import MemoryStore
from services.ollama import LLMService
from services.system_monitor import SystemMonitorService
from services.voice import VoiceService

from core.assistant import Assistant
from core.conversation import ConversationManager
from core.memory import MemoryManager
from core.execution import ExecutionTracker
from core.voice import VoiceCoordinator

from plugins.manager import plugin_manager
from plugins.filesystem import FileSystemPlugin
from plugins.automation import AutomationPlugin
from plugins.system import SystemPlugin
from plugins.terminal import TerminalPlugin
from plugins.browser import BrowserPlugin

from ui.main_window import AetherWindow
from ui.state import AppState, BridgeState


class AetherApplication:
    def __init__(self) -> None:
        self.app_state = AppState()
        self.bridge_state = BridgeState()
        self.qt_app: QApplication | None = None
        self.window: AetherWindow | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._monitor_task: asyncio.Task | None = None
        self._shutdown = False

        self.memory_store = MemoryStore()
        self.llm = LLMService()
        self.system_monitor = SystemMonitorService()
        self.voice_service = VoiceService()

        self.conversation_manager = ConversationManager()
        self.memory_manager = MemoryManager(self.memory_store)
        self.execution_tracker = ExecutionTracker()
        self.voice_coordinator = VoiceCoordinator(self.voice_service)
        self.assistant = Assistant(
            llm=self.llm,
            conversation_manager=self.conversation_manager,
            memory_manager=self.memory_manager,
            execution_tracker=self.execution_tracker,
        )

    def _run_async_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _schedule_coro(self, coro) -> None:
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    def setup(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("AETHER")
        self.qt_app.setOrganizationName("AETHER")

        plugin_manager.register(FileSystemPlugin())
        plugin_manager.register(AutomationPlugin())
        plugin_manager.register(SystemPlugin())
        plugin_manager.register(TerminalPlugin())
        plugin_manager.register(BrowserPlugin())

        self.window = AetherWindow(
            self.app_state,
            self.bridge_state,
            plugin_manager=plugin_manager,
            conversation_manager=self.conversation_manager,
        )
        self.window.setup()

        self.bridge_state.on("user_message", self._on_user_message)

        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

        while self._loop is None:
            pass

        QTimer.singleShot(100, lambda: self._schedule_coro(self._initialize()))

    async def _initialize(self) -> None:
        try:
            await self.memory_store.initialize()
        except Exception as e:
            print(f"[AETHER] Memory init: {e}")
        try:
            await plugin_manager.initialize_all()
        except Exception as e:
            print(f"[AETHER] Plugin init: {e}")
        self._refresh_conversations()
        self._start_monitor()

    def _refresh_conversations(self) -> None:
        if self.window:
            bridge = self.window.get_bridge()
            bridge.refresh_conversations()

    def _start_monitor(self) -> None:
        async def monitor_loop():
            await self.system_monitor.start(self._on_metrics)
        self._monitor_task = asyncio.ensure_future(monitor_loop(), loop=self._loop)

    def _on_metrics(self, metrics: dict) -> None:
        self.app_state.metrics = metrics
        if self.window:
            bridge = self.window.get_bridge()
            bridge.metricsUpdated.emit(metrics)

    def _on_user_message(self, content: str, conversation_id: str = "") -> None:
        async def process():
            bridge = self.window.get_bridge()
            bridge.set_ai_state("thinking")
            conv_id = conversation_id or self.conversation_manager.create()
            if not conversation_id:
                self.app_state.active_conversation_id = conv_id
                bridge.conversationCreated.emit(conv_id, "New Conversation")
                self._refresh_conversations()
            bridge.messageAdded.emit(conv_id, "user", content)
            bridge.refresh_messages()
            async for chunk in self.assistant.process_message(content, conv_id):
                bridge.streamingChunk.emit(chunk)
            self.app_state.active_conversation_id = conv_id
            bridge.messageAdded.emit(conv_id, "assistant", self.conversation_manager.get_messages(conv_id)[-1]["content"])
            bridge.refresh_messages()
            self._refresh_conversations()
            bridge.set_ai_state("idle")
        self._schedule_coro(process())

    def run(self) -> None:
        if self.qt_app:
            sys.exit(self.qt_app.exec())

    def shutdown(self) -> None:
        self._shutdown = True
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._loop and self._loop.is_running():
            self._schedule_coro(self._cleanup())
            self._loop.call_soon_threadsafe(self._loop.stop)

    async def _cleanup(self) -> None:
        try:
            await plugin_manager.shutdown_all()
        except Exception:
            pass
        try:
            await self.memory_store.close()
        except Exception:
            pass
        try:
            await self.llm.close()
        except Exception:
            pass


def main() -> None:
    app = AetherApplication()
    try:
        app.setup()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
