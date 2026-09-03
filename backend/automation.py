from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, unquote, urlparse

from backend.ai_provider import generate_json, model_name
from backend.browser_service import BROWSER_LOCK, connected_browser, new_job_page, read_gmail_message
from backend.candidate_profile import load_candidate_profile
from backend.logging_service import log_ai_interaction, log_error

ROOT = Path(__file__).resolve().parents[1]

IGNORED_HOSTS = {"mail.google.com", "accounts.google.com", "support.google.com", "policies.google.com", "google.com", "www.google.com"}
SUCCESS_TEXT = ("application submitted", "application received", "thank you for applying", "candidatura enviada", "candidatura recebida")


class AutoApplyError(RuntimeError):
    pass


def clean_link(href: str) -> str | None:
    if not href or not href.startswith(("http://", "https://")):
        return None
    parsed = urlparse(href)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"google.com", "www.google.com"} and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [None])[0]
        return clean_link(unquote(target)) if target else None
    if host in IGNORED_HOSTS or host.endswith("googleusercontent.com"):
        return None
    return href


def report_links(message: dict) -> list[dict]:
    unique: dict[str, dict] = {}
    for item in message.get("links", []):
        href = clean_link(str(item.get("href", "")))
        if href:
            unique.setdefault(href, {"link": href, "anchor_text": str(item.get("text", ""))[:500]})
    return list(unique.values())


def parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    return json.loads(cleaned)


def extract_report_jobs(message: dict) -> list[dict]:
    links = report_links(message)
    if not links:
        raise AutoApplyError("O AutoApply Report selecionado não contém links externos de vagas")
    prompt = f"""Extract jobs from the AutoApply Report below. Return valid JSON only:
{{"jobs":[{{"match":"value or UNKNOWN","company":"value or UNKNOWN","role":"value or UNKNOWN","source":"value or domain","link":"exact supplied URL","report_status":"value or UNKNOWN"}}]}}
Include only job or application pages, preserve report values, and never invent information.
REPORT BODY: {message.get('body', '')[:3000]}
LINKS: {json.dumps(links, ensure_ascii=False)}"""
    try:
        response_text = generate_json(prompt)
        log_ai_interaction(
            "extract_report_jobs",
            model_name(),
            prompt,
            response_text,
            {"email_id": message.get("id"), "subject": message.get("subject")},
        )
        parsed = parse_json_response(response_text)
        allowed = {item["link"] for item in links}
        jobs = []
        for raw in parsed.get("jobs", []):
            if raw.get("link") in allowed:
                jobs.append({
                    "match": str(raw.get("match") or "UNKNOWN")[:80],
                    "company": str(raw.get("company") or "UNKNOWN")[:240],
                    "role": str(raw.get("role") or "UNKNOWN")[:240],
                    "source": str(raw.get("source") or urlparse(raw["link"]).netloc)[:160],
                    "link": raw["link"],
                    "report_status": str(raw.get("report_status") or "UNKNOWN")[:160],
                })
        if jobs:
            return jobs
    except Exception as exc:
        log_error("extract_report_jobs", exc, {"email_id": message.get("id"), "subject": message.get("subject")})
        safe_links = [item for item in links if re.search(r"job|jobs|career|careers|apply|application|position|vacanc|vaga", f"{item['link']} {item['anchor_text']}", re.I)]
        if safe_links:
            return [{"match": "UNKNOWN", "company": "UNKNOWN", "role": item["anchor_text"] or "UNKNOWN", "source": urlparse(item["link"]).netloc, "link": item["link"], "report_status": "UNKNOWN"} for item in safe_links]
        raise AutoApplyError(f"A IA não conseguiu extrair as vagas do report: {exc}") from exc
    raise AutoApplyError("Nenhuma vaga válida foi identificada no AutoApply Report")


def _header_key(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", " ", ascii_value.lower().strip())
    aliases = {
        "match": "match", "aderencia": "match", "empresa": "company", "company": "company",
        "vaga": "role", "cargo": "role", "role": "role", "fonte": "source", "source": "source",
        "status": "report_status", "status report": "report_status", "link": "link",
    }
    return aliases.get(normalized, normalized)


def extract_report_jobs_html(message: dict) -> list[dict]:
    """Read jobs directly from report HTML tables without invoking an AI model."""
    jobs: list[dict] = []
    seen: set[str] = set()
    for table in message.get("tables", []):
        headers = [_header_key(str(value)) for value in table.get("headers", [])]
        if not {"company", "role"}.issubset(headers):
            continue
        for row in table.get("rows", []):
            cells = [str(value).strip() for value in row.get("cells", [])]
            values = {headers[index]: value for index, value in enumerate(cells) if index < len(headers)}
            href = next((clean_link(str(item.get("href", ""))) for item in row.get("links", []) if clean_link(str(item.get("href", "")))), None)
            href = href or clean_link(values.get("link", ""))
            if not href or href in seen:
                continue
            seen.add(href)
            jobs.append({
                "match": (values.get("match") or "UNKNOWN")[:80],
                "company": (values.get("company") or "UNKNOWN")[:240],
                "role": (values.get("role") or "UNKNOWN")[:240],
                "source": (values.get("source") or urlparse(href).netloc)[:160],
                "link": href,
                "report_status": (values.get("report_status") or "open")[:160],
            })
    if jobs:
        return jobs
    for item in report_links(message):
        label = item["anchor_text"].strip()
        if re.search(r"job|jobs|career|careers|apply|application|position|vacanc|vaga", f"{item['link']} {label}", re.I):
            jobs.append({"match": "UNKNOWN", "company": "UNKNOWN", "role": label or "UNKNOWN", "source": urlparse(item["link"]).netloc, "link": item["link"], "report_status": "open"})
    if not jobs:
        raise AutoApplyError("Nenhuma vaga válida foi identificada no HTML do AutoApply Report")
    return jobs


def visible_controls(page) -> list[dict]:
    return page.locator("input:not([type=hidden]), textarea, select").evaluate_all("""
    nodes => nodes.filter(n => {
      const r=n.getBoundingClientRect(); const s=getComputedStyle(n);
      return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none';
    }).map((n,index) => {
      const key='autoapply-'+index; n.setAttribute('data-autoapply-field',key);
      const label=(n.labels && n.labels.length ? Array.from(n.labels).map(x=>x.innerText).join(' ') : '') || n.getAttribute('aria-label') || n.placeholder || n.name || n.id || '';
      return {key,label:label.trim().slice(0,500),tag:n.tagName.toLowerCase(),type:(n.type||'text').toLowerCase(),required:!!n.required,value:n.value||'',checked:!!n.checked,options:n.tagName==='SELECT'?Array.from(n.options).map(o=>({value:o.value,text:o.text,disabled:o.disabled})).slice(0,100):[]};
    })
    """)


def local_value(label: str) -> str | None:
    identity = load_candidate_profile()["identity"]
    value = label.lower()
    if "first name" in value or "primeiro nome" in value:
        return identity["first_name"]
    if "last name" in value or "sobrenome" in value:
        return identity["last_name"]
    if "full name" in value or value.strip() in {"name", "nome"}:
        return identity["full_name"]
    if "email" in value:
        return identity["email"]
    if any(term in value for term in ("phone", "telefone", "mobile", "celular")):
        return identity["phone"]
    if value.strip() in {"city", "cidade"}:
        return identity["city"]
    if value.strip() in {"state", "estado"}:
        return identity["state"]
    if value.strip() in {"country", "país", "pais"}:
        return identity["country"]
    return None


def ai_answers(job: dict, controls: list[dict]) -> list[dict]:
    professional_facts = load_candidate_profile()["professional_facts"]
    unresolved = [{key: value for key, value in field.items() if key != "value"} for field in controls]
    prompt = f"""Answer application screening fields using only confirmed facts. Return valid JSON only:
{{"answers":[{{"key":"field key","value":"text or exact option value","decision":"answer|skip|unknown","reason":"brief reason"}}]}}
Rules: never invent; an unknown required field => unknown; optional demographic data => skip/Prefer not to say; a required transcript => unknown; answer in the field's language.
JOB: {json.dumps({k: job[k] for k in ('company','role','source')}, ensure_ascii=False)}
CONFIRMED FACTS: {json.dumps(professional_facts, ensure_ascii=False)}
FIELDS: {json.dumps(unresolved, ensure_ascii=False)}"""
    response_text = generate_json(prompt)
    log_ai_interaction(
        "answer_application_fields",
        model_name(),
        prompt,
        response_text,
        {"company": job.get("company"), "role": job.get("role"), "source": job.get("source")},
    )
    return parse_json_response(response_text).get("answers", [])


def fill_control(page, field: dict, value: str) -> None:
    control = page.locator(f'[data-autoapply-field="{field["key"]}"]').first
    if field["tag"] == "select":
        options = field.get("options", [])
        match = next((item for item in options if item["value"].lower() == value.lower() or item["text"].lower() == value.lower()), None)
        if match:
            control.select_option(match["value"])
    elif field["type"] in {"checkbox", "radio"}:
        if value.lower() in {"true", "yes", "sim", "1", "checked"}:
            control.check()
    elif field["type"] != "file":
        control.fill(value)


def login_priority(page, credential: dict | None = None) -> bool:
    page.wait_for_timeout(800)
    text = page.locator("body").inner_text(timeout=5000).lower()
    linkedin = page.get_by_text(re.compile(r"continue with linkedin|sign in with linkedin|entrar com linkedin", re.I)).first
    if credential and credential.get("login_method") == "linkedin" and linkedin.count() and linkedin.is_visible():
        linkedin.click()
        page.wait_for_timeout(2500)
    google = page.get_by_text(re.compile(r"continue with google|sign in with google|entrar com google", re.I)).first
    if credential and credential.get("login_method") == "google" and google.count() and google.is_visible():
        google.click()
        page.wait_for_timeout(2500)
        account = page.get_by_text(credential["identifier"], exact=False).first
        if account.count() and account.is_visible():
            account.click()
            return True
    if credential:
        identifier = page.locator("input[type=email],input[name*=email i],input[name*=user i],input[autocomplete=username]").first
        password = page.locator("input[type=password],input[autocomplete=current-password]").first
        if identifier.count() and identifier.is_visible():
            identifier.fill(credential["identifier"])
        if password.count() and password.is_visible():
            password.fill(credential["password"])
        submit = page.get_by_role("button", name=re.compile(r"sign in|log in|login|entrar|continuar|continue", re.I)).first
        if submit.count() and submit.is_visible() and submit.is_enabled():
            submit.click()
            page.wait_for_timeout(2500)
        return True
    return "password" not in text and "senha" not in text


def required_invalid(page) -> list[str]:
    return page.locator("input,textarea,select").evaluate_all("nodes => nodes.filter(n => n.required && !n.checkValidity()).map(n => (n.labels&&n.labels[0]&&n.labels[0].innerText)||n.getAttribute('aria-label')||n.name||n.id||'campo obrigatório')")


def action_button(page):
    selectors = [
        re.compile(r"submit application|send application|enviar candidatura|apply now", re.I),
        re.compile(r"review application|review|revisar", re.I),
        re.compile(r"continue|next|save and continue|próximo|continuar", re.I),
    ]
    for pattern in selectors:
        button = page.get_by_role("button", name=pattern).first
        if button.count() and button.is_visible() and button.is_enabled():
            return button, pattern.pattern
    return None, ""


def apply_to_job(context, job: dict, credential: dict | None = None) -> tuple[str, str]:
    page = new_job_page(context, job["link"])
    for _ in range(15):
        if any(marker in page.locator("body").inner_text(timeout=10000).lower() for marker in SUCCESS_TEXT):
            return "applied", "Confirmação de candidatura enviada encontrada no site"
        controls = visible_controls(page)
        if any(field["type"] == "file" and field["required"] and not field["value"] for field in controls):
            return "pending", "Upload obrigatório encontrado; arquivo não configurado"
        for field in controls:
            value = local_value(field["label"])
            if value and not field["value"]:
                fill_control(page, field, value)
        unresolved = [field for field in visible_controls(page) if not field["value"] and field["type"] not in {"hidden", "submit", "button", "file"}]
        if unresolved:
            try:
                answers = ai_answers(job, unresolved)
            except Exception as exc:
                log_error("ai_answers", exc, {"company": job.get("company"), "role": job.get("role"), "link": job.get("link")})
                return "pending", f"A IA não respondeu aos campos: {exc}"
            by_key = {field["key"]: field for field in unresolved}
            for answer in answers:
                field = by_key.get(answer.get("key"))
                if field and answer.get("decision") == "answer":
                    fill_control(page, field, str(answer.get("value", "")))
                elif field and field["required"] and answer.get("decision") == "unknown":
                    return "pending", f"Campo obrigatório desconhecido: {field['label']}"
        invalid = required_invalid(page)
        if invalid:
            if not login_priority(page, credential):
                return "pending", "Login não concluído; configure as credenciais do site na aba Sites"
            invalid = required_invalid(page)
            if invalid:
                return "pending", "Campos obrigatórios não resolvidos: " + ", ".join(invalid[:8])
        button, kind = action_button(page)
        if button is None:
            return "pending", "Botão de continuidade/envio não encontrado"
        button.click()
        page.wait_for_timeout(3000)
        if "submit" in kind or "enviar candidatura" in kind or "apply now" in kind:
            body = page.locator("body").inner_text(timeout=10000).lower()
            if any(marker in body for marker in SUCCESS_TEXT):
                return "applied", "Candidatura enviada e confirmada pelo site"
        time.sleep(0.4)
    return "pending", "Limite de etapas atingido; revisão humana necessária"


def run_autoapply(email_id: str | None, save_application: Callable[[dict, str | None], dict], update_state: Callable[..., None]) -> dict:
    message = read_gmail_message(email_id)
    update_state(email_id=message["id"], message="Extraindo vagas do report com IA...")
    jobs = extract_report_jobs(message)
    update_state(total=len(jobs), message=f"{len(jobs)} vaga(s) encontrada(s)")
    applied = pending = 0
    with BROWSER_LOCK, connected_browser() as (_, context):
        for index, job in enumerate(jobs, start=1):
            update_state(current=index, message=f"Aplicando: {job['company']} · {job['role']}")
            save_application({**job, "application_status": "running", "details": "Automação em andamento"}, message["id"])
            try:
                status, details = apply_to_job(context, job)
            except Exception as exc:
                log_error("apply_to_job", exc, {"company": job.get("company"), "role": job.get("role"), "link": job.get("link")})
                status, details = "pending", f"Automação não concluída: {exc}"
            save_application({**job, "application_status": status, "details": details}, message["id"])
            applied += int(status == "applied")
            pending += int(status != "applied")
            update_state(applied=applied, pending=pending)
    return {"current": len(jobs), "total": len(jobs), "applied": applied, "pending": pending}


def import_report_jobs(email_id: str | None, save_application: Callable[[dict, str | None], dict], update_state: Callable[..., None]) -> dict:
    message = read_gmail_message(email_id)
    update_state(email_id=message["id"], message="Lendo a tabela HTML do report...")
    jobs = extract_report_jobs_html(message)
    for index, job in enumerate(jobs, start=1):
        update_state(current=index, total=len(jobs), message=f"Cadastrando: {job['company']} · {job['role']}")
        save_application({**job, "application_status": "pending", "details": "Importada do HTML do AutoApply Report"}, message["id"])
    return {"current": len(jobs), "total": len(jobs), "applied": 0, "pending": len(jobs)}


def run_job_applications(jobs: list[dict], save_application: Callable[[dict, str | None], dict], update_state: Callable[..., None], credential_lookup: Callable[[str], dict | None]) -> dict:
    applied = pending = 0
    with BROWSER_LOCK, connected_browser() as (_, context):
        for index, job in enumerate(jobs, start=1):
            update_state(current=index, total=len(jobs), message=f"Aplicando com IA: {job['company']} · {job['role']}")
            save_application({**job, "application_status": "running", "details": "Automação com IA em andamento"}, job.get("email_id"))
            try:
                status, details = apply_to_job(context, job, credential_lookup(job["link"]))
            except Exception as exc:
                log_error("apply_to_job", exc, {"company": job.get("company"), "role": job.get("role"), "link": job.get("link")})
                status, details = "pending", f"Automação não concluída: {exc}"
            save_application({**job, "application_status": status, "details": details}, job.get("email_id"))
            applied += int(status == "applied")
            pending += int(status != "applied")
            update_state(applied=applied, pending=pending)
    return {"current": len(jobs), "total": len(jobs), "applied": applied, "pending": pending}
