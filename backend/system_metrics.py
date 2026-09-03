from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong),
        ("memory_load", ctypes.c_ulong),
        ("total_physical", ctypes.c_ulonglong),
        ("available_physical", ctypes.c_ulonglong),
        ("total_page_file", ctypes.c_ulonglong),
        ("available_page_file", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong),
        ("available_virtual", ctypes.c_ulonglong),
        ("available_extended_virtual", ctypes.c_ulonglong),
    ]


class FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]


def _filetime_value(value: FileTime) -> int:
    return (value.high << 32) | value.low


def _cpu_snapshot() -> tuple[int, int, int]:
    idle, kernel, user = FileTime(), FileTime(), FileTime()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        return 0, 0, 0
    return _filetime_value(idle), _filetime_value(kernel), _filetime_value(user)


def cpu_metrics() -> dict:
    first = _cpu_snapshot()
    time.sleep(0.15)
    second = _cpu_snapshot()
    idle = second[0] - first[0]
    total = (second[1] - first[1]) + (second[2] - first[2])
    usage = 0 if total <= 0 else max(0, min(100, (total - idle) * 100 / total))
    return {"usage_percent": round(usage, 1), "logical_cores": os.cpu_count() or 0}


def memory_metrics() -> dict:
    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    used = status.total_physical - status.available_physical
    return {
        "usage_percent": status.memory_load,
        "total_gb": round(status.total_physical / 1024**3, 2),
        "used_gb": round(used / 1024**3, 2),
        "available_gb": round(status.available_physical / 1024**3, 2),
    }


def disk_metrics() -> dict:
    project_root = Path(__file__).resolve().parents[1]
    usage = shutil.disk_usage(project_root.anchor or project_root)
    return {
        "usage_percent": round(usage.used * 100 / usage.total, 1),
        "total_gb": round(usage.total / 1024**3, 1),
        "used_gb": round(usage.used / 1024**3, 1),
        "free_gb": round(usage.free / 1024**3, 1),
    }


def gpu_metrics() -> dict | None:
    candidates = [
        shutil.which("nvidia-smi"),
        r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
        r"C:\Windows\System32\nvidia-smi.exe",
    ]
    executable = next((path for path in candidates if path and Path(path).is_file()), None)
    if not executable:
        return None
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=True,
        )
        name, total, used, utilization = [item.strip() for item in result.stdout.splitlines()[0].split(",")]
        return {
            "name": name,
            "usage_percent": float(utilization),
            "memory_total_mb": int(total),
            "memory_used_mb": int(used),
            "memory_usage_percent": round(int(used) * 100 / max(int(total), 1), 1),
        }
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        return None


def ollama_metrics() -> dict:
    try:
        with urlopen("http://127.0.0.1:11434/api/ps", timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return {"online": False, "models": []}
    models = []
    for model in data.get("models", []):
        size = int(model.get("size", 0))
        size_vram = int(model.get("size_vram", 0))
        models.append(
            {
                "name": model.get("name", ""),
                "size_gb": round(size / 1024**3, 2),
                "vram_gb": round(size_vram / 1024**3, 2),
                "processor": "GPU" if size and size_vram >= size * 0.9 else "CPU + GPU" if size_vram else "CPU",
            }
        )
    return {"online": True, "models": models}


def machine_metrics() -> dict:
    return {
        "cpu": cpu_metrics(),
        "memory": memory_metrics(),
        "gpu": gpu_metrics(),
        "disk": disk_metrics(),
        "ollama": ollama_metrics(),
        "timestamp": time.time(),
    }
