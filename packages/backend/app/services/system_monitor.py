import asyncio
import psutil
from loguru import logger
from app.api.websocket import ConnectionManager


class SystemMonitorService:
    def __init__(self, interval: float = 2.0):
        self.interval = interval

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
                "memory": round(mem.used / 1024 ** 3, 1),
            }
        except Exception:
            return {"usage": 0, "temperature": 0, "memory": 0}

    def get_metrics(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()

        return {
            "cpu": {"usage": cpu, "temperature": 0},
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
                "percentage": round(battery.percent, 1) if battery else 100,
                "charging": battery.power_plugged if battery else True,
            },
            "network": {
                "rx": net.bytes_recv,
                "tx": net.bytes_sent,
            },
            "model": {
                "name": "llama3.2",
                "tokenSpeed": 0,
                "contextUsage": 0,
                "latency": 0,
            },
        }

    async def start(self, manager: ConnectionManager):
        while True:
            try:
                metrics = self.get_metrics()
                await manager.broadcast({
                    "type": "system_metrics",
                    "payload": metrics,
                })
            except Exception as e:
                logger.error(f"System monitor error: {e}")
            await asyncio.sleep(self.interval)
