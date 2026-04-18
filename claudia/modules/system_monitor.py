"""
Módulo: Monitor del sistema.
Reporta CPU, RAM, GPU y disco en lenguaje natural para TTS.
"""

import psutil
from .base import BaseModule


class SystemMonitorModule(BaseModule):
    name = "system_monitor"
    description = "Informa el estado del sistema: CPU, RAM, GPU y espacio en disco"

    def execute(self, action: str, params: dict) -> str:
        return self._full_report()

    def _full_report(self) -> str:
        parts = []

        cpu = psutil.cpu_percent(interval=0.5)
        parts.append(f"el procesador está al {cpu:.0f} por ciento")

        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                    if key in temps and temps[key]:
                        t = temps[key][0].current
                        parts.append(f"temperatura del procesador {t:.0f} grados")
                        break
        except (AttributeError, Exception):
            pass

        ram = psutil.virtual_memory()
        parts.append(
            f"memoria RAM: {ram.used / 1e9:.1f} GB usados "
            f"de {ram.total / 1e9:.1f} GB, al {ram.percent:.0f} por ciento"
        )

        try:
            disk = psutil.disk_usage("/")
            parts.append(
                f"disco: {disk.free / 1e9:.1f} GB libres "
                f"de {disk.total / 1e9:.1f} GB"
            )
        except Exception:
            pass

        gpu_info = self._gpu_info()
        if gpu_info:
            parts.append(gpu_info)

        return "Estado del sistema: " + "; ".join(parts) + "."

    def _gpu_info(self) -> str:
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                g = gpus[0]
                return (
                    f"GPU {g.name}: {g.load * 100:.0f} por ciento de uso, "
                    f"{g.memoryUsed:.0f} MB de {g.memoryTotal:.0f} MB de VRAM, "
                    f"temperatura {g.temperature} grados"
                )
        except ImportError:
            pass
        try:
            import pynvml
            pynvml.nvmlInit()
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            return (
                f"GPU: {util.gpu} por ciento de uso, "
                f"{mem.used / 1e9:.1f} GB VRAM, temperatura {temp} grados"
            )
        except Exception:
            return ""

    def status_line(self) -> str:
        """Línea de una sola línea para la UI de terminal."""
        cpu = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage("/")
            disk_free = f"{disk.free / 1e9:.1f}GB libres"
        except Exception:
            disk_free = "N/A"
        return f"CPU {cpu:4.1f}%  RAM {ram.percent:4.1f}%  Disco {disk_free}"
