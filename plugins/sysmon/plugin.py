"""
AETHER System Monitor Tool
Report detailed system statistics: CPU, RAM, disk, network, battery, processes.
"""

import logging
import platform
import psutil
import time
from datetime import datetime, timedelta

from models.tool_base import ToolBase, ToolObservation

logger = logging.getLogger(__name__)


class SysmonPlugin(ToolBase):

    def name(self) -> str:
        return "sysmon"

    def description(self) -> str:
        return "Detailed system statistics: CPU, RAM, disk, network, processes, battery"

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Category: cpu, memory, disk, network, process, battery, or all"},
            },
        }

    def initialize(self):
        self._boot_time = psutil.boot_time()

    async def execute(self, params: dict) -> ToolObservation:
        start = time.time()
        query = params.get("input", "all").strip().lower()

        if "cpu" in query:
            result = self._cpu_report()
        elif "mem" in query or "ram" in query:
            result = self._memory_report()
        elif "disk" in query:
            result = self._disk_report()
        elif "net" in query:
            result = self._network_report()
        elif "proc" in query or "process" in query:
            result = self._process_report()
        elif "bat" in query:
            result = self._battery_report()
        else:
            result = self._full_report()

        elapsed = (time.time() - start) * 1000
        return ToolObservation(stdout=result, exit_code=0, success=True, execution_time_ms=elapsed)

    def _cpu_report(self) -> str:
        freq = psutil.cpu_freq()
        percent_per_core = psutil.cpu_percent(percpu=True)
        lines = [f"CPU: {platform.processor() or platform.machine()}",
                 f"Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical",
                 f"Usage: {psutil.cpu_percent()}%"]
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
        return (f"RAM Total:     {mem.total / 1e9:.2f} GB\nRAM Used:      {mem.used / 1e9:.2f} GB ({mem.percent}%)\n"
                f"RAM Available: {mem.available / 1e9:.2f} GB\nRAM Cached:    {getattr(mem, 'cached', 0) / 1e9:.2f} GB\n"
                f"\nSwap Total: {swap.total / 1e9:.2f} GB\nSwap Used:  {swap.used / 1e9:.2f} GB ({swap.percent}%)")

    def _disk_report(self) -> str:
        lines = ["Disk Usage:"]
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                bar_fill = int((usage.percent / 100) * 20)
                bar = "█" * bar_fill + "░" * (20 - bar_fill)
                lines.append(f"  {part.device} → {part.mountpoint}\n    [{bar}] {usage.percent}%  Used: {usage.used / 1e9:.1f}GB / {usage.total / 1e9:.1f}GB")
            except PermissionError:
                lines.append(f"  {part.device} (access denied)")
        return "\n".join(lines)

    def _network_report(self) -> str:
        net = psutil.net_io_counters()
        lines = [f"Network I/O:\n  Sent:     {net.bytes_sent / 1e6:.2f} MB\n  Received: {net.bytes_recv / 1e6:.2f} MB",
                 f"  Packets sent: {net.packets_sent:,}\n  Packets recv: {net.packets_recv:,}"]
        lines.append("\nInterfaces:")
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
        lines = ["Top Processes (by CPU):"]
        for p in procs[:15]:
            lines.append(f"  [{p['pid']:5}] {p['name'][:30]:<30} CPU: {p['cpu_percent']:5.1f}%  MEM: {p['memory_percent']:.1f}%")
        return "\n".join(lines)

    def _battery_report(self) -> str:
        bat = psutil.sensors_battery()
        if not bat:
            return "No battery detected (desktop system)"
        status = "Charging" if bat.power_plugged else "Discharging"
        time_left = "Unlimited (plugged in)" if bat.secsleft == psutil.POWER_TIME_UNLIMITED else \
                    "Unknown" if bat.secsleft == psutil.POWER_TIME_UNKNOWN else str(timedelta(seconds=bat.secsleft))
        return f"Battery: {bat.percent:.1f}%\nStatus: {status}\nTime left: {time_left}"

    def _full_report(self) -> str:
        uptime = timedelta(seconds=int(time.time() - self._boot_time))
        return (f"System: {platform.system()} {platform.release()} ({platform.machine()})\n"
                f"Hostname: {platform.node()}\nPython: {platform.python_version()}\nUptime: {uptime}\n\n"
                f"{self._cpu_report()}\n\n{self._memory_report()}")

    def shutdown(self):
        logger.info("Sysmon tool shut down")
