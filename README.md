# AETHER — Native AI Operating System

**AETHER** is a native desktop AI assistant built with Python, PySide6, and Qt Quick (QML). It connects to a local [Ollama](https://ollama.com) instance for fully private, offline AI inference.

---

## Features

| Feature | Status |
|---|---|
| Streaming AI conversation | ✅ |
| SQLite conversation history | ✅ |
| Long-term memory extraction | ✅ |
| Dynamic plugin system | ✅ |
| Terminal execution | ✅ |
| File system browser | ✅ |
| VS Code launcher | ✅ |
| Browser launcher | ✅ |
| System monitoring (CPU/RAM/Disk/Net) | ✅ |
| Python code executor | ✅ |
| Execution timeline | ✅ |
| Voice STT (Faster Whisper) | ✅ |
| Vision / webcam (OpenCV + LLaVA) | ✅ |

---

## Quick Start

### 1. Prerequisites

- **Python 3.12+**
- **Ollama** — [https://ollama.com](https://ollama.com)
- **A model pulled in Ollama**:

```bash
ollama pull llama3.2
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Ollama

```bash
ollama serve
```

### 4. Launch AETHER

```bash
python app.py
```

---

## Architecture

```
AETHER/
├── app.py                  # Entry point
├── core/
│   ├── application.py      # App orchestrator
│   ├── initializer.py      # Startup sequence (QThread)
│   └── bridge.py           # QML ↔ Python bridge
├── ui/
│   ├── splash.py           # Splash screen
│   └── qml/                # All QML UI files
│       ├── Main.qml
│       ├── TopBar.qml
│       ├── Sidebar.qml
│       ├── ConversationPanel.qml
│       ├── MessageBubble.qml
│       ├── CommandInput.qml
│       ├── ExecutionTimeline.qml
│       ├── SettingsPanel.qml
│       ├── MemoryPanel.qml
│       ├── SettingsSection.qml
│       └── SuggestionChip.qml
├── database/
│   └── db_manager.py       # SQLite manager
├── services/
│   ├── ollama_service.py   # Streaming Ollama client
│   ├── conversation_service.py
│   ├── memory_service.py
│   ├── plugin_manager.py
│   └── system_monitor.py
├── models/
│   └── plugin_base.py      # Plugin ABC
├── plugins/
│   ├── terminal/           # Shell command execution
│   ├── filesystem/         # File browsing & I/O
│   ├── vscode/             # VS Code launcher
│   ├── browser/            # Web browser launcher
│   ├── sysmon/             # System stats
│   ├── voice/              # STT + TTS
│   ├── vision/             # Webcam + image AI
│   ├── memory/             # Memory management
│   └── executor/           # Python code runner
└── utils/
    └── logging_config.py
```

---

## Plugin Development

Create a directory under `plugins/yourplugin/` with a `plugin.py`:

```python
from models.plugin_base import PluginBase

class MyPlugin(PluginBase):
    def initialize(self): ...
    async def execute(self, payload: dict) -> str: ...
    def shutdown(self): ...
    def metadata(self) -> dict:
        return {
            "name": "myplugin",
            "description": "Does something useful",
            "version": "1.0.0",
            "icon": "🔌",
            "category": "general",
        }
```

AETHER auto-discovers it on next launch.

---

## Voice Setup (Optional)

1. Install [Faster Whisper](https://github.com/guillaumekln/faster-whisper): `pip install faster-whisper`
2. Download [Piper TTS](https://github.com/rhasspy/piper/releases) binary
3. Download a Piper voice model from [HuggingFace](https://huggingface.co/rhasspy/piper-voices)
4. Configure the model path in Settings

---

## Vision Setup (Optional)

1. Pull a vision model: `ollama pull llava`
2. OpenCV is auto-installed via requirements.txt

---

## Data Storage

All data is stored in `~/.aether/`:
- `aether.db` — SQLite database (conversations, memory, settings)
- `logs/aether.log` — Application log

---

## License

MIT
