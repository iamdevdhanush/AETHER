from __future__ import annotations
import os
from pathlib import Path


class Settings:
    app_name: str = "AETHER"
    app_version: str = "0.1.0"
    debug: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    memory_db_path: str = "aether_memory.db"
    memory_enabled: bool = True
    system_monitor_interval: float = 2.0

    def __init__(self) -> None:
        self.app_name = os.getenv("AETHER_APP_NAME", self.app_name)
        self.app_version = os.getenv("AETHER_APP_VERSION", self.app_version)
        self.debug = os.getenv("AETHER_DEBUG", str(self.debug)).lower() == "true"
        self.ollama_base_url = os.getenv("AETHER_OLLAMA_BASE_URL", self.ollama_base_url)
        self.ollama_model = os.getenv("AETHER_OLLAMA_MODEL", self.ollama_model)
        self.memory_db_path = os.getenv("AETHER_MEMORY_DB_PATH", self.memory_db_path)
        self.memory_enabled = os.getenv("AETHER_MEMORY_ENABLED", str(self.memory_enabled)).lower() == "true"
        self.system_monitor_interval = float(os.getenv("AETHER_SYSTEM_MONITOR_INTERVAL", str(self.system_monitor_interval)))

        # Load .env if present
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


settings = Settings()
