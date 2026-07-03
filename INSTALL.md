# AETHER Installation Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| Python | 3.12 | 3.12+ |
| RAM | 8 GB | 16 GB+ |
| Storage | 10 GB free | 20 GB+ |
| GPU | Optional | NVIDIA for faster inference |

---

## Step 1: Install Python 3.12

Download from https://python.org/downloads/

Verify:
```bash
python --version
# Python 3.12.x
```

---

## Step 2: Install Ollama

Download from https://ollama.com and install.

Start Ollama:
```bash
ollama serve
```

Pull a model (required):
```bash
ollama pull llama3.2
```

Optional models:
```bash
ollama pull mistral        # Alternative LLM
ollama pull codellama      # Code-specialized
ollama pull llava          # Vision support
```

---

## Step 3: Clone / Extract AETHER

```bash
# If from ZIP:
unzip AETHER-v1.zip
cd AETHER

# If from git:
git clone <repo>
cd AETHER
```

---

## Step 4: Create Virtual Environment (Recommended)

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

---

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `PySide6` (Qt framework)
- `httpx` (HTTP client)
- `aiofiles` (async file I/O)
- `psutil` (system monitoring)
- `opencv-python` (vision)
- `faster-whisper` (voice STT)
- `Pillow` (screenshots)

**Note:** `faster-whisper` requires ~100MB download for the Whisper model on first use.

---

## Step 6: Launch

```bash
python app.py
```

AETHER will:
1. Show splash screen
2. Initialize database at `~/.aether/aether.db`
3. Connect to Ollama
4. Load plugins
5. Open workspace

---

## Troubleshooting

### "Cannot connect to Ollama"
- Ensure `ollama serve` is running in another terminal
- Verify with: `curl http://localhost:11434/api/tags`

### "No module named PySide6"
- Run: `pip install PySide6`
- On Linux you may need: `sudo apt install libgl1-mesa-dev libglib2.0-0`

### "Failed to load Main.qml"
- Ensure you're running from the AETHER root directory
- Check `~/.aether/logs/aether.log` for details

### Voice not working
- Piper TTS requires manual download (it's a binary, not a pip package)
- See README.md Voice Setup section

### Vision not working
- Run: `pip install opencv-python Pillow`
- For LLaVA: `ollama pull llava`

---

## Optional: Voice Setup

1. Download Piper binary from https://github.com/rhasspy/piper/releases
2. Extract and add to PATH, or place in project root
3. Download a voice model:
   - https://huggingface.co/rhasspy/piper-voices
   - Recommended: `en_US-lessac-medium.onnx`
4. Install audio support: `pip install sounddevice scipy`

---

## Data Location

```
~/.aether/
├── aether.db          # All conversations, memory, settings
└── logs/
    └── aether.log     # Application log
```

To reset AETHER completely: delete `~/.aether/`
