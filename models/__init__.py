from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AICoreState(str, Enum):
    idle = "idle"
    listening = "listening"
    thinking = "thinking"
    executing = "executing"
    speaking = "speaking"
    error = "error"
    success = "success"


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class SystemMetrics:
    cpu: dict = field(default_factory=lambda: {"usage": 0, "temperature": 0})
    gpu: dict = field(default_factory=lambda: {"usage": 0, "temperature": 0, "memory": 0})
    ram: dict = field(default_factory=lambda: {"used": 0, "total": 0, "percentage": 0})
    disk: dict = field(default_factory=lambda: {"used": 0, "total": 0, "percentage": 0})
    battery: dict = field(default_factory=lambda: {"percentage": 0, "charging": False})
    network: dict = field(default_factory=lambda: {"rx": 0, "tx": 0})
    model: dict = field(default_factory=lambda: {"name": "llama3.2", "tokenSpeed": 0, "contextUsage": 0, "latency": 0})


@dataclass
class Message:
    id: str
    role: str  # user | assistant | system
    content: str
    timestamp: float
    metadata: Optional[dict] = None


@dataclass
class Conversation:
    id: str
    title: str
    messages: list = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class ExecutionStep:
    id: str
    label: str
    status: StepStatus = StepStatus.pending
    details: Optional[str] = None


@dataclass
class PluginInfo:
    id: str
    name: str
    description: str
    version: str
    enabled: bool = True
    plugin_type: str = "system"


@dataclass
class Memory:
    id: str
    content: str
    type: str = "conversation"
    timestamp: float = 0.0
    embeddings: Optional[list[float]] = None


@dataclass
class AppSettings:
    voice: dict = field(default_factory=lambda: {
        "wakeWord": True,
        "continuousListening": False,
        "pushToTalk": True,
    })
    models: dict = field(default_factory=lambda: {
        "provider": "ollama",
        "modelName": "llama3.2",
        "baseUrl": "http://localhost:11434",
    })
    memory: dict = field(default_factory=lambda: {
        "enabled": True,
        "vectorSearch": False,
    })
    appearance: dict = field(default_factory=lambda: {
        "reducedMotion": False,
    })
    permissions: dict = field(default_factory=lambda: {
        "executeCommands": False,
        "fileOperations": False,
        "systemControl": False,
    })
    hotkeys: dict = field(default_factory=lambda: {
        "toggleAether": "Ctrl+Shift+A",
        "pushToTalk": "Ctrl+Shift+V",
        "screenshot": "Ctrl+Shift+S",
    })
    system: dict = field(default_factory=lambda: {
        "startOnBoot": False,
        "minimizeToTray": True,
    })
