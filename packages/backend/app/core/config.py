from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AETHER"
    app_version: str = "0.1.0"
    debug: bool = False

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    memory_db_path: str = "aether_memory.db"
    memory_enabled: bool = True

    system_monitor_interval: float = 2.0

    class Config:
        env_prefix = "AETHER_"
        env_file = ".env"


settings = Settings()
