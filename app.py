"""
AETHER - Native AI Operating System
Entry point: python app.py
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QIcon, QFont, QFontDatabase

from core.application import AetherApplication
from utils.logging_config import setup_logging


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("AETHER starting...")

    QCoreApplication.setApplicationName("AETHER")
    QCoreApplication.setApplicationVersion("1.0.0")
    QCoreApplication.setOrganizationName("AETHER")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # High DPI
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Load fonts
    fonts_dir = PROJECT_ROOT / "ui" / "assets" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))
        for font_file in fonts_dir.glob("*.otf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Set application icon
    icon_path = PROJECT_ROOT / "ui" / "assets" / "icons" / "aether.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Launch AETHER
    aether = AetherApplication(app, PROJECT_ROOT)
    aether.launch()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
