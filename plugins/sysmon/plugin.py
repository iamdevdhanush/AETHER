"""
AETHER System Monitor Plugin
Report detailed system statistics.
"""

import logging
import platform
import psutil
import time
from datetime import datetime, timedelta

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class SysmonPlugin(PluginBase):
    """
    Retrieve and format system statistics including CPU, memory,
    disk, network, battery, and process information.
    """

    def initialize(self):
        self._boot_time = psutil.boot_time()
        logger.info("Sysmon plugin initialized")

    async def execute(self, payload: dict) -> str:
        query = payload.get("input", "all").strip().lower()

        if "cpu" in query:
            return self._cpu_report()
        elif "mem" in query or "ram" in query:
            return self._memory_report()
        elif "disk" in query:
            return self._disk_report()
        elif "net" in query:
            return self._network_report()
        elif "proc" in query or "process" in query:
            return self._process_report()
        elif "bat" in query:
            return self._battery_report()
        else:
            return self._full_report()

    def _cpu_report(self) -> str:
        freq = psutil.cpu_freq()
        percent_per_core = psutil.cpu_percent(percpu=True)
        lines = [
            f"CPU: {platform.processor() or platform.machine()}",
            f"Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical",
            f"Usage: {psutil.cpu_percent()}%",
        ]
        if freq:
            lines.append(f"Frequency: {freq.current:.0f} MHz (max: {freq.max:.0f} MHz)")
        lines.append("Per-core usage:")
        for i, p in enumerate(percent_per_core):
            bar = "█" * int(p / 5) + "░" * (20 - int(p / 5))
            lines.append(f"  Core {i}: [{bar}] {p}%")
        return "\n".join(lines)

    def _memory_report(self) -> str:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return (
            f"RAM Total:     {mem.total / 1e9:.2f} GB\n"
            f"RAM Used:      {mem.used / 1e9:.2f} GB ({mem.percent}%)\n"
            f"RAM Available: {mem.available / 1e9:.2f} GB\n"
            f"RAM Cached:    {getattr(mem, 'cached', 0) / 1e9:.2f} GB\n"
            f"\nSwap Total: {swap.total / 1e9:.2f} GB\n"
            f"Swap Used:  {swap.used / 1e9:.2f} GB ({swap.percent}%)"
        )

    def _disk_report(self) -> str:
        lines = ["Disk Usage:"]
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                bar_fill = int((usage.percent / 100) * 20)
                bar = "█" * bar_fill + "░" * (20 - bar_fill)
                lines.append(
                    f"  {part.device} → {part.mountpoint}\n"
                    f"    [{bar}] {usage.percent}%  "
                    f"Used: {usage.used / 1e9:.1f}GB / {usage.total / 1e9:.1f}GB"
                )
            except PermissionError:
                lines.append(f"  {part.device} (access denied)")
        return "\n".join(lines)

    def _network_report(self) -> str:
        net = psutil.net_io_counters()
        lines = [
            f"Network I/O:",
            f"  Sent:     {net.bytes_sent / 1e6:.2f} MB",
            f"  Received: {net.bytes_recv / 1e6:.2f} MB",
            f"  Packets sent: {net.packets_sent:,}",
            f"  Packets recv: {net.packets_recv:,}",
            "\nNetwork Interfaces:",
        ]
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family.name == "AF_INET":
                    lines.append(f"  {name}: {addr.address}")
        return "\n".join(lines)

    def _process_report(self) -> str:
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda p: p.get("cpu_percent", 0), reverse=True)

        lines = [f"Top Processes (by CPU):"]
        for p in procs[:15]:
            lines.append(
                f"  [{p['pid']:5}] {p['name'][:30]:<30} "
                f"CPU: {p['cpu_percent']:5.1f}%  "
                f"MEM: {p['memory_percent']:.1f}%"
            )
        return "\n".join(lines)

    def _battery_report(self) -> str:
        bat = psutil.sensors_battery()
        if not bat:
            return "No battery detected (desktop system)"
        status = "Charging" if bat.power_plugged else "Discharging"
        if bat.secsleft == psutil.POWER_TIME_UNLIMITED:
            time_left = "Unlimited (plugged in)"
        elif bat.secsleft == psutil.POWER_TIME_UNKNOWN:
            time_left = "Unknown"
        else:
            time_left = str(timedelta(seconds=bat.secsleft))
        return (
            f"Battery: {bat.percent:.1f}%\n"
            f"Status: {status}\n"
            f"Time left: {time_left}"
        )

    def _full_report(self) -> str:
        uptime = timedelta(seconds=int(time.time() - self._boot_time))
        system_info = (
            f"System: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"Hostname: {platform.node()}\n"
            f"Python: {platform.python_version()}\n"
            f"Uptime: {uptime}\n\n"
        )
        return system_info + self._cpu_report() + "\n\n" + self._memory_report()

    def shutdown(self):
        logger.info("Sysmon plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "sysmon",
            "description": "Detailed system statistics: CPU, RAM, disk, network, processes",
            "version": "1.0.0",
            "icon": "📊",
            "category": "system",
        }
