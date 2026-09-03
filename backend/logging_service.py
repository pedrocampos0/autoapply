from __future__ import annotations

import json
import sys
import threading
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_ROOT = ROOT / "logs"
SUCCESS_DIR = LOG_ROOT / "sucessos"
ERROR_DIR = LOG_ROOT / "erros"
_LOCK = threading.Lock()


def initialize_logs() -> None:
    SUCCESS_DIR.mkdir(parents=True, exist_ok=True)
    ERROR_DIR.mkdir(parents=True, exist_ok=True)


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return repr(value)


def log_ai_interaction(operation: str, model: str, prompt: str, response: str, metadata: dict | None = None) -> Path:
    initialize_logs()
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": "local_ai_interaction",
        "operation": operation,
        "model": model,
        "prompt": prompt,
        "response": response,
        "metadata": _json_safe(metadata or {}),
        "security": "Cookies and passwords are never included by the logger.",
    }
    path = SUCCESS_DIR / f"ia-{_stamp()}-{uuid.uuid4().hex[:8]}.json"
    with _LOCK:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def log_error(context: str, error: BaseException, metadata: dict | None = None) -> Path:
    initialize_logs()
    trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": "unexpected_error",
        "context": context,
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": trace,
        "metadata": _json_safe(metadata or {}),
    }
    path = ERROR_DIR / f"erro-{_stamp()}-{uuid.uuid4().hex[:8]}.json"
    with _LOCK:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def install_exception_hooks() -> None:
    initialize_logs()
    previous_sys_hook = sys.excepthook

    def sys_hook(exc_type, exc_value, exc_traceback):
        error = exc_value if isinstance(exc_value, BaseException) else Exception(str(exc_value))
        error.__traceback__ = exc_traceback
        log_error("sys.excepthook", error)
        previous_sys_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = sys_hook

    if hasattr(threading, "excepthook"):
        previous_thread_hook = threading.excepthook

        def thread_hook(args):
            log_error(f"thread:{args.thread.name if args.thread else 'unknown'}", args.exc_value)
            previous_thread_hook(args)

        threading.excepthook = thread_hook
