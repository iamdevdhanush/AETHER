# AETHER Architecture Document

## Overview

AETHER is a native Windows desktop AI assistant following **Clean Architecture** principles. All concerns are cleanly separated into layers with unidirectional dependencies.

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                             │
│   QML (Qt Quick) + PySide6 Widgets                         │
│   Main.qml, TopBar, Sidebar, ConversationPanel, ...        │
└────────────────────┬────────────────────────────────────────┘
                     │ signals / slots
┌────────────────────▼────────────────────────────────────────┐
│                   Bridge Layer                              │
│   core/bridge.py (QMLBridge : QObject)                     │
│   All QML↔Python I/O flows through here                    │
└────────┬─────────────────┬──────────────────────────────────┘
         │                 │
┌────────▼───────┐ ┌───────▼────────────────────────────────┐
│  Core Layer    │ │         Services Layer                  │
│  application   │ │  OllamaService   ConversationService   │
│  initializer   │ │  MemoryService   PluginManager         │
│  bridge        │ │  SystemMonitor                         │
└────────┬───────┘ └───────┬────────────────────────────────┘
         │                 │
┌────────▼─────────────────▼────────────────────────────────┐
│                   Data Layer                              │
│   DatabaseManager (SQLite)                                │
│   Tables: conversations, messages, memories,              │
│           settings, plugin_data, execution_timeline       │
└───────────────────────────────────────────────────────────┘
         │
┌────────▼───────────────────────────────────────────────────┐
│                  Plugin Layer                              │
│   PluginBase (ABC)                                        │
│   terminal | filesystem | vscode | browser | sysmon       │
│   voice    | vision     | memory | executor               │
└────────────────────────────────────────────────────────────┘
```

---

## Startup Sequence

```
python app.py
    │
    ▼
AetherApplication.launch()
    │
    ▼
SplashScreen.show()
    │
    ▼
SystemInitializer.run() [QThread]
    ├── DatabaseManager.initialize()
    ├── OllamaService()
    ├── MemoryService(db)
    ├── ConversationService(db, ollama, memory)
    ├── PluginManager.discover_and_load()
    └── SystemMonitorService.start()
    │
    ▼
AetherApplication._launch_workspace()
    ├── SplashScreen.close()
    ├── QQmlApplicationEngine()
    ├── QMLBridge(services)
    └── engine.load("Main.qml")
    │
    ▼
Main.qml renders
    └── bridge.loadConversations()
    └── bridge.loadPlugins()
```

---

## Thread Model

| Thread | Purpose |
|--------|---------|
| Main (Qt) | UI rendering, event loop, signal dispatch |
| SystemInitializer (QThread) | Startup initialization |
| AsyncWorker (QThread per call) | Each bridge operation runs in its own thread with its own asyncio event loop |
| SystemMonitor | Polled via QTimer on main thread |

**Why AsyncWorker per call?**  
httpx async I/O (Ollama streaming) requires an asyncio event loop. Qt's main thread cannot block. Each bridge call spawns a short-lived QThread that creates its own event loop, runs the coroutine, and emits Qt signals back to the main thread — safe and non-blocking.

---

## Data Flow: Message Send

```
User types message
    │
CommandInput.qml → onSendMessage signal
    │
QMLBridge.sendMessage(text)   [main thread]
    │
AsyncWorker spawned           [new QThread]
    │
    ├── bridge.messageReceived.emit("user", text)
    │       → ConversationPanel.appendMessage()
    │
    ├── ConversationService.add_message(user)
    │
    ├── MemoryService.get_relevant_memories(text)
    │
    ├── OllamaService.stream_chat()
    │   └── for chunk in stream:
    │           bridge.streamChunk.emit(chunk)
    │               → ConversationPanel.appendStreamChunk()
    │
    ├── bridge.streamComplete.emit()
    │       → ConversationPanel.finalizeStream()
    │
    ├── ConversationService.add_message(assistant)
    │
    └── MemoryService.extract_and_store()
```

---

## Plugin Interface

```python
class PluginBase(ABC):
    def initialize(self) -> None: ...       # Called on load
    async def execute(self, payload: dict) -> Any: ...  # Main logic
    def shutdown(self) -> None: ...         # Called on exit
    def metadata(self) -> dict: ...         # Plugin info
    def settings(self) -> dict: ...         # Config schema
```

Plugins are discovered by scanning `plugins/*/plugin.py` for `PluginBase` subclasses. Dynamic import via `importlib`.

---

## Database Schema

```sql
conversations   (id, title, model, created_at, updated_at, archived)
messages        (id, conversation_id, role, content, created_at, token_count)
memories        (id, content, source, importance, created_at, accessed_at, access_count)
memory_tags     (memory_id, tag)
settings        (key, value, updated_at)
plugin_data     (plugin_name, key, value, updated_at)
execution_timeline (id, event_type, description, metadata, created_at)
```

WAL mode enabled for concurrent reads during streaming writes.

---

## QML Component Tree

```
Main.qml (Window)
├── TopBar.qml
├── Sidebar.qml
│   └── [ListView of conversations]
├── ConversationPanel.qml
│   ├── [ListView of messages]
│   │   └── MessageBubble.qml (delegate)
│   └── [Welcome / empty state]
│       └── SuggestionChip.qml
├── ExecutionTimeline.qml
│   └── [ListView of events]
├── CommandInput.qml
│   └── [Plugin quick-launch buttons]
├── SettingsPanel.qml (overlay)
│   └── SettingsSection.qml (×N)
└── MemoryPanel.qml (overlay)
    └── [ListView of memories]
```

---

## Key Design Decisions

1. **No FastAPI / no web server** — Direct Python↔QML via `QObject` signals/slots. Zero network overhead for UI.

2. **No Electron** — Native Qt renders at 60fps, uses ~1/5 the RAM of Electron.

3. **Async per call, not per app** — Each bridge operation owns its asyncio loop in a QThread. Simpler than a single persistent loop shared with Qt.

4. **SQLite WAL** — Write-ahead logging allows concurrent reads during Ollama response streaming.

5. **Plugin ABC** — Strict interface enforcement. Every capability is a plugin; core code has zero feature knowledge.

6. **Memory by pattern** — Simple regex extraction avoids running a second LLM call per message. Fast, offline, deterministic.
