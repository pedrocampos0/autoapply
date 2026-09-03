from __future__ import annotations

import hashlib
import os
import re
import threading
from contextlib import contextmanager
from urllib.parse import quote

from playwright.sync_api import Browser, Page, Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright

CDP_URL = "http://127.0.0.1:9222"
GMAIL_QUERY = 'subject:"AutoApply Report"'
LINKEDIN_HOME_URL = "https://www.linkedin.com/feed/"
BROWSER_LOCK = threading.RLock()


class BrowserConnectionError(RuntimeError):
    pass


def gmail_account() -> str:
    account = os.getenv("GMAIL_ACCOUNT", "").strip()
    if not account:
        raise BrowserConnectionError("Configure GMAIL_ACCOUNT in .env before reading AutoApply reports.")
    return account


def gmail_url(account_index: int) -> str:
    return f"https://mail.google.com/mail/u/{account_index}/#search/{quote(GMAIL_QUERY)}"


def _gmail_account_label(page: Page) -> str:
    account_button = page.locator(
        "a[aria-label*='Google Account'], a[aria-label*='Conta do Google'], "
        "button[aria-label*='Google Account'], button[aria-label*='Conta do Google']"
    ).first
    if not account_button.count():
        return ""
    try:
        return account_button.get_attribute("aria-label") or ""
    except Exception:
        return ""


@contextmanager
def connected_browser():
    playwright: Playwright | None = None
    try:
        playwright = sync_playwright().start()
        browser: Browser = playwright.chromium.connect_over_cdp(CDP_URL, timeout=10_000)
        if not browser.contexts:
            raise BrowserConnectionError("O perfil Chrome do AutoApply não está disponível")
        yield browser, browser.contexts[0]
    except BrowserConnectionError:
        raise
    except Exception as exc:
        raise BrowserConnectionError(
            "Não foi possível conectar ao Chrome do AutoApply. Feche e abra o aplicativo novamente."
        ) from exc
    finally:
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass


def dashboard_page(context) -> Page | None:
    return next((page for page in context.pages if page.url.startswith("http://127.0.0.1:8000")), None)


def gmail_page(context) -> Page:
    expected_account = gmail_account()
    page = next((item for item in context.pages if "mail.google.com" in item.url), None)
    if page is None:
        page = context.new_page()
    candidates = [gmail_url(account_index) for account_index in range(10)]
    loaded = False
    for candidate in candidates:
        try:
            page.goto(candidate, wait_until="domcontentloaded", timeout=30_000)
            body_text = page.locator("body").inner_text(timeout=5_000)
            if "Temporary Error (404)" in body_text or "Erro temporário (404)" in body_text:
                continue
            page.wait_for_selector(
                "a[aria-label*='Google Account'], a[aria-label*='Conta do Google'], "
                "button[aria-label*='Google Account'], button[aria-label*='Conta do Google'], "
                "input[type=email], tr.zA",
                timeout=15_000,
            )
            if page.locator("input[type=email]").count() or "accounts.google.com" in page.url:
                continue
            account_label = _gmail_account_label(page)
            if not account_label or expected_account.lower() not in account_label.lower():
                continue
            loaded = True
            page.wait_for_timeout(1_500)
            break
        except PlaywrightTimeoutError:
            continue
    if not loaded:
        raise BrowserConnectionError("O Gmail não respondeu. Confirme que a conta está aberta no Chrome do AutoApply.")
    if page.locator("input[type=email]").count() or "accounts.google.com" in page.url:
        raise BrowserConnectionError(f"Entre na conta {expected_account} no Chrome do AutoApply e tente novamente.")
    account_button = page.locator("a[aria-label*='Google Account'], a[aria-label*='Conta do Google']").first
    if account_button.count():
        account_label = account_button.get_attribute("aria-label") or ""
        if expected_account.lower() not in account_label.lower():
            raise BrowserConnectionError(f"O Gmail aberto não é {expected_account}. Troque a conta no Chrome e tente novamente.")
    return page


def _row_text(row, selector: str) -> str:
    locator = row.locator(selector).first
    if not locator.count():
        return ""
    try:
        return locator.inner_text(timeout=2_000).strip()
    except Exception:
        return ""


def _message_id(index: int, sender: str, subject: str, date: str) -> str:
    digest = hashlib.sha256(f"{sender}|{subject}|{date}".encode("utf-8")).hexdigest()[:16]
    return f"{index}:{digest}"


def gmail_messages(limit: int = 30) -> list[dict]:
    with BROWSER_LOCK, connected_browser() as (_, context):
        dashboard = dashboard_page(context)
        page = gmail_page(context)
        rows = page.locator("tr.zA")
        messages: list[dict] = []
        for index in range(min(rows.count(), limit)):
            row = rows.nth(index)
            subject = _row_text(row, ".bog")
            if "autoapply report" not in subject.lower():
                continue
            sender = _row_text(row, ".zF, .yP")
            snippet = _row_text(row, ".y2")
            date_node = row.locator("td.xW span").first
            date = ""
            if date_node.count():
                date = (date_node.get_attribute("title") or _row_text(row, "td.xW span")).strip()
            messages.append(
                {
                    "id": _message_id(index, sender, subject, date),
                    "index": index,
                    "sender": sender,
                    "subject": subject,
                    "date": date,
                    "snippet": snippet,
                }
            )
        if dashboard is not None:
            dashboard.bring_to_front()
        return messages


def read_gmail_message(email_id: str | None) -> dict:
    with BROWSER_LOCK, connected_browser() as (_, context):
        page = gmail_page(context)
        rows = page.locator("tr.zA")
        if rows.count() == 0:
            raise BrowserConnectionError("Nenhum e-mail com assunto AutoApply Report foi encontrado")
        index = 0
        if email_id:
            try:
                index = int(email_id.split(":", 1)[0])
            except ValueError as exc:
                raise BrowserConnectionError("A seleção de e-mail expirou. Atualize a lista e tente novamente.") from exc
        if index < 0 or index >= rows.count():
            raise BrowserConnectionError("O e-mail selecionado não está mais na lista. Atualize e tente novamente.")
        row = rows.nth(index)
        subject = _row_text(row, ".bog")
        if "autoapply report" not in subject.lower():
            raise BrowserConnectionError("O e-mail selecionado não é um AutoApply Report")
        row.click()
        try:
            page.wait_for_selector("div.a3s", timeout=20_000)
        except PlaywrightTimeoutError as exc:
            raise BrowserConnectionError("Não foi possível abrir o conteúdo do AutoApply Report") from exc
        bodies = page.locator("div.a3s")
        body = "\n\n".join(text.strip() for text in bodies.all_inner_texts() if text.strip())
        links = bodies.locator("a[href]").evaluate_all(
            "nodes => nodes.map(n => ({href:n.href, text:(n.innerText || n.textContent || '').trim()}))"
        )
        tables = bodies.locator("table").evaluate_all("""
            tables => tables.map(table => {
              const rows = [...table.querySelectorAll('tr')];
              return {
                headers: rows[0] ? [...rows[0].querySelectorAll('th,td')].map(cell => (cell.innerText || cell.textContent || '').trim()) : [],
                rows: rows.slice(1).map(row => ({
                  cells: [...row.querySelectorAll('th,td')].map(cell => (cell.innerText || cell.textContent || '').trim()),
                  links: [...row.querySelectorAll('a[href]')].map(link => ({href: link.href, text: (link.innerText || link.textContent || '').trim()}))
                })).filter(row => row.cells.some(Boolean) || row.links.length)
              };
            }).filter(table => table.rows.length)
        """)
        sender = ""
        sender_node = page.locator("span.gD").first
        if sender_node.count():
            sender = sender_node.get_attribute("email") or sender_node.inner_text()
        return {
            "id": email_id or _message_id(index, sender, subject, ""),
            "subject": subject,
            "sender": sender,
            "body": body[:40_000],
            "links": links,
            "tables": tables,
            "gmail_url": page.url,
        }


def new_job_page(context, url: str) -> Page:
    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.bring_to_front()
    return page


def read_linkedin_profile() -> dict:
    with BROWSER_LOCK, connected_browser() as (_, context):
        dashboard = dashboard_page(context)
        page = next((item for item in context.pages if "linkedin.com/in/" in item.url), None)
        configured_url = os.getenv("LINKEDIN_PROFILE_URL", "").strip()
        if page is None:
            page = context.new_page()
            page.goto(configured_url or LINKEDIN_HOME_URL, wait_until="domcontentloaded", timeout=45_000)
        elif configured_url and page.url.rstrip("/") != configured_url.rstrip("/"):
            page.goto(configured_url, wait_until="domcontentloaded", timeout=45_000)
        try:
            page.wait_for_selector("main, input[name=session_key]", timeout=25_000)
        except PlaywrightTimeoutError as exc:
            raise BrowserConnectionError("O LinkedIn não respondeu no perfil Chrome do AutoApply") from exc
        if page.locator("input[name=session_key]").count() or "/login" in page.url:
            raise BrowserConnectionError("Entre no LinkedIn no Chrome do AutoApply e tente novamente")
        if "/in/" not in page.url:
            me_button = page.locator("button.global-nav__primary-link-me-menu-trigger, button[aria-label*='Me'], button[aria-label*='Eu']").first
            if me_button.count() and me_button.is_visible():
                me_button.click()
                view_profile = page.get_by_text(re.compile(r"^View Profile$|^Ver perfil$", re.I)).first
                if view_profile.count() and view_profile.is_visible():
                    view_profile.click()
                    page.wait_for_load_state("domcontentloaded", timeout=30_000)
            if "/in/" not in page.url:
                own_link = page.locator("a[href*='/in/']").first
                if own_link.count():
                    href = own_link.get_attribute("href")
                    if href:
                        page.goto(href, wait_until="domcontentloaded", timeout=45_000)
        if "/in/" not in page.url:
            raise BrowserConnectionError("Não foi possível localizar o seu perfil. Abra o perfil no LinkedIn e tente novamente.")
        for _ in range(8):
            page.evaluate("window.scrollBy(0, Math.max(700, window.innerHeight * 0.8))")
            page.wait_for_timeout(350)
        page.evaluate("window.scrollTo(0, 0)")
        main = page.locator("main").first
        profile_text = main.inner_text(timeout=15_000).strip() if main.count() else ""
        name = ""
        headline = ""
        name_node = page.locator("main h1").first
        if name_node.count():
            name = name_node.inner_text().strip()
        headline_node = page.locator("main .text-body-medium").first
        if headline_node.count():
            headline = headline_node.inner_text().strip()
        result = {
            "connected": True,
            "url": page.url,
            "name": name,
            "headline": headline,
            "profile_text": profile_text[:60_000],
        }
        if dashboard is not None:
            dashboard.bring_to_front()
        return result
