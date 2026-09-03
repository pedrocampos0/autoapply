from __future__ import annotations

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from backend.ai_provider import context_length, model_name


class JobSearchError(RuntimeError):
    pass


class _VisibleText(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if tag == "a" and not self.hidden:
            href = next((value for key, value in attrs if key == "href"), None)
            if href:
                self.parts.append(f"LINK: {urljoin(self.base_url, href)}")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def _page_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 AutoApply/2.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read(2_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    parser = _VisibleText(url)
    parser.feed(raw)
    return "\n".join(parser.parts)[:80_000]


def _json_object(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return json.loads(cleaned)


def _canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "referrer"}
    query = urlencode([(key, item) for key, item in parse_qsl(parts.query) if key.lower() not in tracking])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def discover_jobs(instructions_path: Path, existing_links: set[str], source_urls: list[str]) -> list[dict]:
    if not instructions_path.is_file():
        raise JobSearchError("BUSCAR_VAGAS.md ainda não foi encontrado na raiz do projeto")
    instructions = instructions_path.read_text(encoding="utf-8-sig").strip()
    urls = list(dict.fromkeys([*re.findall(r"https?://[^\s)>\]}]+", instructions), *source_urls]))
    if not urls:
        raise JobSearchError("Cadastre e ative pelo menos um site na aba Sites antes de buscar vagas")
    try:
        from llama_index.core import Document, SummaryIndex
        from llama_index.core.settings import Settings
        from llama_index.llms.ollama import Ollama
    except ImportError as exc:
        raise JobSearchError("Dependências do LlamaIndex não estão instaladas. Execute a atualização de requirements.txt") from exc

    documents = []
    failures = []
    for url in urls[:20]:
        try:
            documents.append(Document(text=_page_text(url), metadata={"url": url}))
        except Exception as exc:
            failures.append(f"{url}: {exc}")
    if not documents:
        raise JobSearchError("Nenhuma fonte de BUSCAR_VAGAS.md pôde ser lida: " + "; ".join(failures[:3]))

    Settings.llm = Ollama(
        model=model_name(),
        base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        request_timeout=300,
        context_window=context_length(),
    )
    index = SummaryIndex.from_documents(documents)
    prompt = f"""Siga estas instruções de busca de vagas:
{instructions[:12_000]}

Analise apenas os documentos indexados. Retorne JSON válido no formato:
{{"jobs":[{{"match":"percentual ou UNKNOWN","company":"empresa","role":"cargo","source":"fonte","link":"URL exata da vaga","report_status":"open","snippet":"resumo curto"}}]}}
Não invente URLs. Ignore estes links já cadastrados: {json.dumps(sorted(existing_links), ensure_ascii=False)[:12_000]}
"""
    response = index.as_query_engine(response_mode="tree_summarize").query(prompt)
    parsed = _json_object(str(response))
    jobs = []
    seen = {_canonical_url(link) for link in existing_links}
    for raw in parsed.get("jobs", []):
        link = str(raw.get("link", "")).strip()
        canonical = _canonical_url(link)
        if not link.startswith(("http://", "https://")) or canonical in seen:
            continue
        seen.add(canonical)
        jobs.append({
            "match": str(raw.get("match") or "UNKNOWN")[:80],
            "company": str(raw.get("company") or "UNKNOWN")[:240],
            "role": str(raw.get("role") or "UNKNOWN")[:240],
            "source": str(raw.get("source") or "LlamaIndex")[:160],
            "link": link[:2000],
            "report_status": str(raw.get("report_status") or "open")[:160],
            "snippet": str(raw.get("snippet") or "")[:1000],
        })
    return jobs
