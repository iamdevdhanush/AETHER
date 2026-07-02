from __future__ import annotations
from typing import Any, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal, Slot, Property
from ui.state import AppState, BridgeState

if TYPE_CHECKING:
    from plugins.manager import PluginManager
    from core.conversation import ConversationManager


class ApplicationBridge(QObject):
    splashFinished = Signal()
    viewChanged = Signal(str)
    aiStateChanged = Signal(str)
    amplitudeChanged = Signal(float)
    metricsUpdated = Signal(dict)
    conversationCreated = Signal(str, str)
    messageAdded = Signal(str, str, str)
    streamingChunk = Signal(str)
    executionStepChanged = Signal(str, str, str)
    settingsChanged = Signal()
    connectionChanged = Signal(bool)
    conversationsUpdated = Signal()
    messagesUpdated = Signal()
    pluginsUpdated = Signal()

    def __init__(
        self,
        app_state: AppState,
        bridge_state: BridgeState,
        plugin_manager: Any = None,
        conversation_manager: Any = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._state = app_state
        self._bridge = bridge_state
        self._plugin_manager = plugin_manager
        self._conversation_manager = conversation_manager

    def _get_nested(self, key: str) -> Any:
        keys = key.split(".")
        target = self._state.settings
        for k in keys:
            target = target[k]
        return target

    def _set_nested(self, key: str, value: Any) -> None:
        keys = key.split(".")
        target = self._state.settings
        for k in keys[:-1]:
            target = target[k]
        target[keys[-1]] = value
        self.settingsChanged.emit()

    @Slot()
    def finish_splash(self) -> None:
        self._state.show_splash = False
        self.splashFinished.emit()

    @Slot(str)
    def set_view(self, view: str) -> None:
        self._state.current_view = view
        self.viewChanged.emit(view)

    @Slot(str)
    def set_ai_state(self, state: str) -> None:
        self._state.ai_state = state
        self.aiStateChanged.emit(state)

    def set_amplitude(self, amplitude: float) -> None:
        self._state.amplitude = amplitude
        self.amplitudeChanged.emit(amplitude)

    def update_metrics(self, metrics: dict) -> None:
        self._state.metrics = metrics
        self.metricsUpdated.emit(metrics)

    @Slot(str, str)
    def send_message(self, content: str, conversation_id: str = "") -> None:
        self._bridge.emit("user_message", content, conversation_id)

    @Slot(str)
    def set_listening(self, listening: bool) -> None:
        self._state.is_listening = listening
        self._bridge.emit("listening_changed", listening)

    @Slot(str, object)
    def update_setting(self, key: str, value: Any) -> None:
        self._set_nested(key, value)

    @Slot()
    def create_conversation(self) -> None:
        if not self._conversation_manager:
            return
        conv_id = self._conversation_manager.create()
        conv = self._conversation_manager.conversations[conv_id]
        self._state.active_conversation_id = conv_id
        self._state.conversations = self._conversation_manager.get_recent()
        self.conversationCreated.emit(conv_id, conv.title)
        self.conversationsUpdated.emit()

    @Slot(str)
    def select_conversation(self, conv_id: str) -> None:
        if not self._conversation_manager:
            return
        self._state.active_conversation_id = conv_id
        self._conversation_manager.set_active(conv_id)
        self.messagesUpdated.emit()
        self.set_view("chat")

    @Slot(str)
    def toggle_plugin(self, plugin_id: str) -> None:
        if not self._plugin_manager:
            return
        info = self._plugin_manager.get_info(plugin_id)
        if info:
            if info.enabled:
                self._plugin_manager.disable(plugin_id)
            else:
                self._plugin_manager.enable(plugin_id)
            self.pluginsUpdated.emit()

    @Slot(str)
    def execute_quick_action(self, action_name: str) -> None:
        action_map = {
            "Take Screenshot": ("plugins.vision", "capture"),
            "System Status": ("plugins.system", "status"),
            "Open Terminal": ("plugins.terminal", "open"),
        }
        entry = action_map.get(action_name)
        if entry and self._plugin_manager:
            plugin_id, action = entry
            plugin = self._plugin_manager.get(plugin_id)
            if plugin:
                self._bridge.emit("quick_action", plugin_id, action)

    def refresh_conversations(self) -> None:
        if self._conversation_manager:
            self._state.conversations = self._conversation_manager.get_recent()
            self.conversationsUpdated.emit()

    def refresh_messages(self) -> None:
        self.messagesUpdated.emit()

    def get_view(self) -> str:
        return self._state.current_view

    def get_ai_state(self) -> str:
        return self._state.ai_state

    def get_metrics(self) -> dict:
        return self._state.metrics

    def get_amplitude(self) -> float:
        return self._state.amplitude

    def get_settings(self) -> dict:
        return self._state.settings

    def get_conversations(self) -> list[dict]:
        return self._state.conversations

    def get_plugins(self) -> list[dict]:
        if self._plugin_manager:
            return self._plugin_manager.get_all_infos()
        return []

    def get_messages(self) -> list[dict]:
        conv_id = self._state.active_conversation_id
        if conv_id and self._conversation_manager:
            return self._conversation_manager.get_messages(conv_id)
        return []

    def get_current_conversation_id(self) -> str:
        return self._state.active_conversation_id or ""

    view = Property(str, get_view, set_view, notify=viewChanged)
    aiState = Property(str, get_ai_state, set_ai_state, notify=aiStateChanged)
    settings = Property("QVariant", get_settings, notify=settingsChanged)
    conversations = Property("QVariant", get_conversations, notify=conversationsUpdated)
    plugins = Property("QVariant", get_plugins, notify=pluginsUpdated)
    messages = Property("QVariant", get_messages, notify=messagesUpdated)
    metrics = Property("QVariant", get_metrics, notify=metricsUpdated)
    currentConversationId = Property(str, get_current_conversation_id, notify=messagesUpdated)
