from __future__ import annotations
import time
import uuid


class AppState:
    def __init__(self) -> None:
        self.show_splash: bool = True
        self.current_view: str = "home"
        self.ai_state: str = "idle"
        self.amplitude: float = 0.0
        self.is_listening: bool = False
        self.is_speaking: bool = False
        self.is_connected: bool = False
        self.is_streaming: bool = False

        self.metrics: dict = {
            "cpu": {"usage": 0, "temperature": 0},
            "gpu": {"usage": 0, "temperature": 0, "memory": 0},
            "ram": {"used": 0, "total": 0, "percentage": 0},
            "disk": {"used": 0, "total": 0, "percentage": 0},
            "battery": {"percentage": 0, "charging": False},
            "network": {"rx": 0, "tx": 0},
            "model": {"name": "llama3.2", "tokenSpeed": 0, "contextUsage": 0, "latency": 0},
        }

        self.conversations: list[dict] = []
        self.active_conversation_id: str | None = None
        self.execution_steps: list[dict] = []

        self.settings: dict = {
            "voice": {"wakeWord": True, "continuousListening": False, "pushToTalk": True},
            "models": {"provider": "ollama", "modelName": "llama3.2", "baseUrl": "http://localhost:11434"},
            "memory": {"enabled": True, "vectorSearch": False},
            "appearance": {"reducedMotion": False},
            "permissions": {"executeCommands": False, "fileOperations": False, "systemControl": False},
            "hotkeys": {"toggleAether": "Ctrl+Shift+A", "pushToTalk": "Ctrl+Shift+V", "screenshot": "Ctrl+Shift+S"},
            "system": {"startOnBoot": False, "minimizeToTray": True},
        }

        self.health_history: list[dict] = []


class BridgeState:
    def __init__(self) -> None:
        self._callbacks: dict[str, list[callable]] = {}

    def on(self, event: str, callback: callable) -> None:
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def emit(self, event: str, *args, **kwargs) -> None:
        for cb in self._callbacks.get(event, []):
            cb(*args, **kwargs)

    def remove(self, event: str, callback: callable) -> None:
        self._callbacks.get(event, []).remove(callback)
