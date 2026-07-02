from __future__ import annotations
import asyncio
import psutil
from services.config import settings


class SystemMonitorService:
    def __init__(self, interval: float | None = None) -> None:
        self.interval = interval or settings.system_monitor_interval

    def get_gpu_info(self) -> dict:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "usage": util.gpu,
                "temperature": temp,
                "memory": round(mem.used / 1024**3, 1),
            }
        except Exception:
            return {"usage": 0, "temperature": 0, "memory": 0}

    def get_metrics(self) -> dict:
        cpu_usage = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()

        return {
            "cpu": {"usage": cpu_usage, "temperature": 0},
            "gpu": self.get_gpu_info(),
            "ram": {
                "used": ram.used,
                "total": ram.total,
                "percentage": ram.percent,
            },
            "disk": {
                "used": disk.used,
                "total": disk.total,
                "percentage": disk.percent,
            },
            "battery": {
                "percentage": battery.percent if battery else 0,
                "charging": battery.power_plugged if battery else False,
            },
            "network": {"rx": net.bytes_recv, "tx": net.bytes_sent},
            "model": {
                "name": settings.ollama_model,
                "tokenSpeed": 0,
                "contextUsage": 0,
                "latency": 0,
            },
        }

    async def start(self, callback) -> None:
        while True:
            metrics = self.get_metrics()
            callback(metrics)
            await asyncio.sleep(self.interval)
