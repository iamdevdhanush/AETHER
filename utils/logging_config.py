"""
AETHER Logging Configuration
Sets up structured logging to both console and file.
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(level: int = logging.INFO):
    """
    Configure application-wide logging.
    Logs go to both the console and a rotating file.
    """
    log_dir = Path.home() / ".aether" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "aether.log"

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers
    root.handlers.clear()

    # ── Console handler ──────────────────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # ── File handler (rotating, 5 MB × 3 backups) ────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    ))
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    logging.info(f"AETHER logging initialized → {log_file}")
