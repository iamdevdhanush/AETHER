"""
AETHER System Monitor Service
Tracks CPU, RAM, GPU, disk, network usage via psutil.
"""

import logging
import time
from typing import Optional

import psutil

from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


class SystemMonitorService(QObject):
    """
    Polls system metrics and emits them as Qt signals.
    Connected to the QML bridge for real-time UI updates.
    """

    stats_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._timer: Optional[QTimer] = None
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()

    def start(self):
        self._running = True
        logger.info("System monitor started")

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.stop()
        logger.info("System monitor stopped")

    def update(self):
        """Collect current metrics and emit stats_ready signal."""
        if not self._running:
            return

        try:
            stats = self._collect_stats()
            self.stats_ready.emit(stats)
        except Exception as e:
            logger.error(f"System monitor error: {e}")

    def _collect_stats(self) -> dict:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk
        disk = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        # Network
        net = psutil.net_io_counters()
        now = time.time()
        elapsed = max(now - self._last_net_time, 0.001)
        net_sent_speed = (net.bytes_sent - self._last_net.bytes_sent) / elapsed
        net_recv_speed = (net.bytes_recv - self._last_net.bytes_recv) / elapsed
        self._last_net = net
        self._last_net_time = now

        # Processes (top 5 by CPU)
        top_procs = []
        try:
            procs = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            top_procs = sorted(procs, key=lambda p: p.get("cpu_percent", 0), reverse=True)[:5]
        except Exception:
            pass

        return {
            "cpu": {
                "percent": round(cpu_percent, 1),
                "freq_mhz": round(cpu_freq.current, 0) if cpu_freq else 0,
                "cores_logical": cpu_count,
                "cores_physical": cpu_physical,
            },
            "memory": {
                "total_gb": round(mem.total / 1e9, 2),
                "used_gb": round(mem.used / 1e9, 2),
                "available_gb": round(mem.available / 1e9, 2),
                "percent": mem.percent,
                "swap_total_gb": round(swap.total / 1e9, 2),
                "swap_used_gb": round(swap.used / 1e9, 2),
            },
            "disk": {
                "total_gb": round(disk.total / 1e9, 2),
                "used_gb": round(disk.used / 1e9, 2),
                "free_gb": round(disk.free / 1e9, 2),
                "percent": round(disk.percent, 1),
            },
            "network": {
                "sent_mb": round(net.bytes_sent / 1e6, 2),
                "recv_mb": round(net.bytes_recv / 1e6, 2),
                "sent_speed_kbps": round(net_sent_speed / 1024, 1),
                "recv_speed_kbps": round(net_recv_speed / 1024, 1),
            },
            "top_processes": top_procs,
            "timestamp": int(time.time() * 1000),
        }

    def get_current_stats(self) -> dict:
        """Synchronous snapshot of current stats."""
        try:
            return self._collect_stats()
        except Exception as e:
            logger.error(f"get_current_stats error: {e}")
            return {}
