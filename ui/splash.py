"""
AETHER Splash Screen
Shown during initialization with animated progress.
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush

logger = logging.getLogger(__name__)


class SplashScreen(QWidget):
    """
    Custom splash screen shown during AETHER initialization.
    Displays logo, version, and initialization status.
    """

    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self._status_text = "Initializing..."
        self._progress = 0
        self._pulse = 0.0

        self._setup_window()
        self._setup_ui()
        self._start_animation()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(520, 320)

        # Center on screen
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                (geo.width() - self.width()) // 2,
                (geo.height() - self.height()) // 2,
            )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title label
        self.title_label = QLabel("AETHER", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "color: #E8E8FF; font-size: 52px; font-weight: 700; "
            "letter-spacing: 12px; background: transparent;"
        )

        # Subtitle
        self.subtitle_label = QLabel("AI Operating System", self)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet(
            "color: #8080BB; font-size: 13px; letter-spacing: 4px; "
            "background: transparent;"
        )

        # Status
        self.status_label = QLabel(self._status_text, self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #6060AA; font-size: 11px; background: transparent;"
        )

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1A1A2E;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4040AA, stop:1 #8080FF
                );
                border-radius: 1px;
            }
        """)

        layout.addStretch(2)
        layout.addWidget(self.title_label)
        layout.addSpacing(8)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)
        layout.addWidget(self.status_label)
        layout.addSpacing(16)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(20)

    def _start_animation(self):
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(50)
        self._pulse_timer.timeout.connect(self._animate)
        self._pulse_timer.start()

    def _animate(self):
        self._pulse = (self._pulse + 0.05) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Background
        painter.setBrush(QBrush(QColor(10, 10, 22)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 16, 16)

        # Subtle gradient overlay
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(20, 20, 45, 180))
        grad.setColorAt(1, QColor(5, 5, 15, 180))
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(0, 0, w, h, 16, 16)

        # Border glow
        pen = QPen(QColor(60, 60, 120, 120))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 16, 16)

        painter.end()

    def set_status(self, message: str):
        self._status_text = message
        self.status_label.setText(message)
        logger.debug(f"Splash: {message}")
