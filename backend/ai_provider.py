from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama2:7b-chat-q2_K"
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "llama_config.json"
ALLOWED_CONTEXTS = {512, 1024, 2048, 4096}
CONFIG_LOCK = threading.Lock()


class LocalAIError(RuntimeError):
    pass


def _gpu_layer_candidates() -> list[int]:
    """Prefer partial GPU offload and degrade gracefully on fragmented VRAM."""
    try:
        preferred = max(0, min(32, int(os.getenv("OLLAMA_NUM_GPU", "24"))))
    except ValueError:
        preferred = 24
    return list(dict.fromkeys((preferred, 16, 8, 0)))


def model_name() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def context_length() -> int:
    try:
        value = int(json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get("context_length", 2048))
        return value if value in ALLOWED_CONTEXTS else 2048
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 2048


def save_context_length(value: int) -> int:
    if value not in ALLOWED_CONTEXTS:
        raise ValueError("Use um contexto de 512, 1024, 2048 ou 4096 tokens")
    with CONFIG_LOCK:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps({"context_length": value}, indent=2), encoding="utf-8")
    return value


def generate_json(prompt: str, timeout: int = 300) -> str:
    base_url = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    context = context_length()
    payload = json.dumps(
        {
            "model": model_name(),
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": -1,
            "options": {"temperature": 0.1, "num_ctx": context, "num_predict": min(768, context // 2), "num_gpu": _gpu_layer_candidates()[0]},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:1000]
        if "out-of-memory" in details or "failed to allocate" in details:
            raise LocalAIError(
                f"Memória insuficiente para carregar o Llama 2 com contexto {context} tokens. "
                "Feche aplicativos pesados ou reduza o contexto e tente novamente."
            ) from exc
        raise LocalAIError(f"Ollama recusou a solicitação (HTTP {exc.code}): {details}") from exc
    except URLError as exc:
        raise LocalAIError("O Ollama local não está disponível. Feche e abra o AutoApply novamente.") from exc
    except TimeoutError as exc:
        raise LocalAIError("O Llama 2 demorou mais de 5 minutos para responder.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LocalAIError("O Ollama retornou uma resposta inválida.") from exc

    text = result.get("response")
    if not isinstance(text, str) or not text.strip():
        raise LocalAIError(f"O Llama 2 não gerou conteúdo: {result.get('error', 'erro desconhecido')}")
    return text.strip()


def chat(messages: list[dict], timeout: int = 300) -> dict:
    base_url = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    context = context_length()
    payload = json.dumps(
        {
            "model": model_name(),
            "messages": messages,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": 0.7,
                "num_ctx": context,
                "num_predict": min(768, context // 2),
                "num_gpu": _gpu_layer_candidates()[0],
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:1000]
        if "out-of-memory" in details or "failed to allocate" in details:
            raise LocalAIError(
                f"Memória insuficiente para carregar o Llama 2 com contexto {context} tokens. "
                "Feche aplicativos pesados ou reduza o contexto e tente novamente."
            ) from exc
        raise LocalAIError(f"Ollama recusou a solicitação (HTTP {exc.code}): {details}") from exc
    except URLError as exc:
        raise LocalAIError("O Ollama local não está disponível. Feche e abra o AutoApply novamente.") from exc
    except TimeoutError as exc:
        raise LocalAIError("O Llama 2 demorou mais de 5 minutos para responder.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LocalAIError("O Ollama retornou uma resposta inválida.") from exc

    content = result.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise LocalAIError(f"O Llama 2 não gerou conteúdo: {result.get('error', 'erro desconhecido')}")
    eval_duration = result.get("eval_duration", 0) / 1_000_000_000
    return {
        "content": content.strip(),
        "model": result.get("model", model_name()),
        "context_length": context,
        "metrics": {
            "total_duration_ms": round(result.get("total_duration", 0) / 1_000_000, 1),
            "load_duration_ms": round(result.get("load_duration", 0) / 1_000_000, 1),
            "prompt_tokens": result.get("prompt_eval_count", 0),
            "response_tokens": result.get("eval_count", 0),
            "tokens_per_second": round(result.get("eval_count", 0) / max(eval_duration, 0.001), 2),
        },
    }
