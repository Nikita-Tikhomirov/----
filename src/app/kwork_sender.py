from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlparse

import websocket

logger = logging.getLogger(__name__)

PRICE_PATTERN = re.compile(
    r"(?:цена|бюджет|стоимост[ьи]|ориентир|за)\D{0,24}(\d[\d\s]{2,9})(?:\s*(?:руб|р\b|₽))",
    re.IGNORECASE,
)
DAYS_PATTERN = re.compile(r"(?:за|срок|сделаю|готов(?:о)?)\D{0,24}(\d{1,2})\s*(?:дн|день|дня|дней)", re.IGNORECASE)
PHONE_LIKE_PATTERN = re.compile(r"(?:\+?\d[\s-]?){10,}")


@dataclass(frozen=True)
class ReplyTerms:
    price_rub: int | None = None
    days: int | None = None


class KworkProjectUnavailableError(RuntimeError):
    """Raised when Kwork no longer exposes the project to receive a reply."""


class KworkReplySender:
    can_send_replies = True

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        cdp_url: str = "http://127.0.0.1:9222",
        browser_profile_dir: str = "",
        login_email: str = "",
        login_password: str = "",
    ):
        self.timeout_seconds = timeout_seconds
        self.cdp_url = cdp_url.rstrip("/")
        self.browser_profile_dir = browser_profile_dir
        self.login_email = login_email
        self.login_password = login_password

    def send_message(
        self,
        contact: str,
        text: str,
        *,
        price_rub: int | None = None,
        days: int | None = None,
        title: str = "",
    ) -> str:
        return self.send_reply(
            contact,
            text,
            price_rub=price_rub,
            days=days,
            title=title,
            submit=True,
        )

    def prepare_reply(
        self,
        contact: str,
        text: str,
        price_rub: int | None = None,
        days: int | None = None,
        title: str = "",
    ) -> str:
        return self.send_reply(contact, text, price_rub=price_rub, days=days, title=title, submit=False)

    def send_reply(
        self,
        contact: str,
        text: str,
        price_rub: int | None = None,
        days: int | None = None,
        title: str = "",
        submit: bool = True,
    ) -> str:
        if not _is_kwork_project_url(contact):
            raise ValueError("Kwork sender requires a Kwork project URL")
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Kwork reply text must not be empty")
        offer_url = _offer_url(contact)

        from app import kwork_source

        kwork_source._ensure_chrome_cdp(self.cdp_url, contact, self.browser_profile_dir)
        page = kwork_source._find_or_create_page(self.cdp_url, contact, tab_kind="project")
        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=self.timeout_seconds)
        try:
            if not self._try_open_direct_offer(ws, offer_url):
                try:
                    ws.close()
                except Exception:
                    pass
                page = kwork_source._find_or_create_page(self.cdp_url, contact, tab_kind="project")
                ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=self.timeout_seconds)
                kwork_source._refresh_page(ws, contact, self.timeout_seconds)
                self._wait_for_page_text(ws)
                known_page_ids = _page_ids(kwork_source._cdp_json(self.cdp_url, "/json/list", timeout=5) or [])
                self._open_reply_form(ws)
                ws = self._switch_to_offer_page(ws, offer_url, known_page_ids=known_page_ids)
                self._wait_for_page_text(ws)
                self._wait_for_reply_field(ws)
            page_text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
            has_field = bool(kwork_source._evaluate(ws, _HAS_REPLY_FIELD_SCRIPT))
            login_message = _login_required_message(page_text, has_reply_field=has_field)
            if login_message:
                self._auto_login_or_raise(ws, offer_url, login_message)
                self._open_reply_form(ws)
                self._wait_for_reply_field(ws)
                page_text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
                has_field = bool(kwork_source._evaluate(ws, _HAS_REPLY_FIELD_SCRIPT))
                login_message = _login_required_message(page_text, has_reply_field=has_field)
                if login_message:
                    raise RuntimeError(login_message)
            extracted_terms = _extract_reply_terms(clean_text)
            terms = ReplyTerms(
                price_rub=price_rub if price_rub is not None else extracted_terms.price_rub,
                days=days if days is not None else extracted_terms.days,
            )
            project_title = (title or self._project_title(ws)).strip()
            submit_result = self._fill_and_submit(ws, clean_text, terms, project_title, submit=submit)
            if not submit_result.get("ok"):
                reason = submit_result.get("reason") or "Kwork submit button was not found"
                raise RuntimeError(str(reason))
            project_id = _project_id(contact)
            if not submit:
                return f"kwork-project-{project_id}-prepared"
            self._confirm_after_submit(ws)
            self._wait_after_submit(ws)
            return f"kwork-project-{project_id}"
        finally:
            ws.close()

    def _try_open_direct_offer(self, ws, offer_url: str) -> bool:
        from app import kwork_source

        try:
            kwork_source._refresh_page(ws, offer_url, min(self.timeout_seconds, 8))
            self._wait_for_page_text(ws)
            self._wait_for_reply_field(ws)
            return True
        except KworkProjectUnavailableError:
            raise
        except Exception as exc:
            logger.info("Kwork direct offer page failed, falling back to project button: %s", exc)
            return False

    def _switch_to_offer_page(self, ws, offer_url: str, known_page_ids: set[str] | None = None):
        from app import kwork_source

        project_id = _offer_project_id(offer_url)
        started_at = time.monotonic()
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            current_url = str(kwork_source._evaluate(ws, "location.href") or "")
            if _is_kwork_inbox_url(current_url):
                raise RuntimeError("Kwork opened inbox instead of the offer form; this project may already have a reply.")
            if _is_offer_page_for_project(current_url, project_id) or kwork_source._evaluate(ws, _HAS_REPLY_FIELD_SCRIPT):
                return ws
            pages = kwork_source._cdp_json(self.cdp_url, "/json/list", timeout=5) or []
            inbox_seen = False
            for page in pages:
                page_url = page.get("url", "")
                socket_url = page.get("webSocketDebuggerUrl")
                page_id = str(page.get("id", ""))
                if _is_kwork_inbox_url(page_url):
                    inbox_seen = True
                    if known_page_ids is not None and page_id not in known_page_ids:
                        raise RuntimeError(
                            "Kwork opened inbox instead of the offer form; this project may already have a reply."
                        )
                if socket_url and _is_offer_page_for_project(page_url, project_id):
                    new_ws = websocket.create_connection(socket_url, timeout=self.timeout_seconds)
                    ws.close()
                    return new_ws
            if inbox_seen and time.monotonic() - started_at > 5:
                raise RuntimeError("Kwork opened inbox instead of the offer form; this project may already have a reply.")
            time.sleep(0.5)
        return ws

    def _wait_for_page_text(self, ws) -> None:
        from app import kwork_source

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
            unavailable_message = _project_unavailable_message(text)
            if unavailable_message:
                raise KworkProjectUnavailableError(unavailable_message)
            if len(text.strip()) > 100:
                return
            time.sleep(0.4)
        raise RuntimeError("Kwork project page did not render readable text")

    def _open_reply_form(self, ws) -> None:
        from app import kwork_source

        kwork_source._evaluate(ws, _OPEN_REPLY_FORM_SCRIPT)

    def _auto_login_or_raise(self, ws, contact: str, login_message: str) -> None:
        if not self.login_email or not self.login_password:
            raise RuntimeError(login_message)

        from app import kwork_source

        payload = json.dumps(
            {
                "email": self.login_email,
                "password": self.login_password,
            },
            ensure_ascii=False,
        )
        result = kwork_source._evaluate(ws, f"({_AUTO_LOGIN_SCRIPT})({payload})")
        data = json.loads(result) if isinstance(result, str) else {"started": False, "reason": "no result"}
        if not data.get("started"):
            raise RuntimeError(str(data.get("reason") or login_message))
        self._wait_for_login(ws)
        kwork_source._refresh_page(ws, contact, self.timeout_seconds)
        self._wait_for_page_text(ws)

    def _wait_for_login(self, ws) -> None:
        from app import kwork_source

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
            has_profile = bool(
                re.search(r"\b(?:Кворки|Заказы|Чат|Мои отклики|Коннекты|Профиль)\b", text, re.IGNORECASE)
            )
            logged_out = "вход" in text.lower() and "регистрация" in text.lower()
            if has_profile and not logged_out:
                return
            time.sleep(0.5)
        raise RuntimeError("Kwork auto-login did not finish; captcha or manual confirmation may be required")

    def _wait_for_reply_field(self, ws) -> None:
        from app import kwork_source

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if kwork_source._evaluate(ws, _HAS_REPLY_FIELD_SCRIPT):
                return
            text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
            unavailable_message = _project_unavailable_message(text)
            if unavailable_message:
                raise KworkProjectUnavailableError(unavailable_message)
            if _login_required_message(text, has_reply_field=False):
                return
            time.sleep(0.5)
        raise RuntimeError("Kwork reply field was not found")

    def _project_title(self, ws) -> str:
        from app import kwork_source

        title = str(
            kwork_source._evaluate(
                ws,
                """
                (() => {
                  const cardTitle = document.querySelector('.want-card h1, h1, .want-card__title')?.innerText || '';
                  return (cardTitle || document.title || '').replace(/\\s+-\\s+Kwork\\s*$/i, '').trim();
                })()
                """,
            )
            or ""
        )
        return title[:70]

    def _fill_and_submit(self, ws, text: str, terms: ReplyTerms, title: str = "", submit: bool = True) -> dict:
        from app import kwork_source

        payload = json.dumps(
            {
                "text": text,
                "title": title,
                "price": "" if terms.price_rub is None else str(terms.price_rub),
                "days": "" if terms.days is None else str(terms.days),
                "submit": submit,
            },
            ensure_ascii=False,
        )
        result = kwork_source._evaluate(ws, f"({_FILL_AND_SUBMIT_SCRIPT})({payload})")
        if isinstance(result, str):
            return json.loads(result)
        return {"submitted": False, "reason": "Kwork submit script returned no result"}

    def _confirm_after_submit(self, ws) -> None:
        from app import kwork_source

        deadline = time.monotonic() + min(self.timeout_seconds, 5)
        while time.monotonic() < deadline:
            result = kwork_source._evaluate(ws, _CONFIRM_SUBMIT_SCRIPT)
            data = json.loads(result) if isinstance(result, str) else {"ok": True}
            if data.get("blocked"):
                raise RuntimeError(str(data.get("reason") or "Kwork requires manual confirmation"))
            if data.get("clicked"):
                time.sleep(0.8)
                continue
            if not data.get("hasDialog"):
                return
            time.sleep(0.4)

    def _wait_after_submit(self, ws) -> None:
        from app import kwork_source

        deadline = time.monotonic() + min(self.timeout_seconds, 10)
        while time.monotonic() < deadline:
            text = str(kwork_source._evaluate(ws, "document.body && document.body.innerText") or "")
            lowered = text.lower()
            if re.search(
                r"(предложени[ея]\s+отправлен|отклик\s+отправлен|"
                r"ваш[ее]?\s+предложени[ея]\s+(?:отправлен|размещен|принят)|"
                r"успешно\s+отправлен)",
                lowered,
            ):
                return
            if any(marker in lowered for marker in ("sms", "смс", "captcha", "капч", "верификац", "код подтверждения")):
                raise RuntimeError("Kwork requires manual confirmation before sending the reply")
            if any(marker in lowered for marker in ("обязательное поле", "заполните", "ошибка")):
                raise RuntimeError("Kwork did not accept the reply; check required fields in the opened project tab")
            time.sleep(0.5)
        raise RuntimeError("Kwork reply was not confirmed as sent; check the opened tab for confirmation or errors")


def _extract_reply_terms(text: str) -> ReplyTerms:
    without_phones = PHONE_LIKE_PATTERN.sub(" ", text)
    price = _first_int(PRICE_PATTERN, without_phones)
    days = _first_int(DAYS_PATTERN, without_phones)
    if price is not None and price < 500:
        price = None
    if days is not None and not 1 <= days <= 30:
        days = None
    return ReplyTerms(price_rub=price, days=days)


def _first_int(pattern: re.Pattern[str], text: str) -> int | None:
    match = pattern.search(text)
    if not match:
        return None
    value = re.sub(r"\D", "", match.group(1))
    return int(value) if value else None


def _login_required_message(page_text: str, has_reply_field: bool) -> str:
    lowered = page_text.lower()
    if has_reply_field:
        return ""
    if "вход" in lowered and "регистрация" in lowered and "предложить услугу" in lowered:
        return "Kwork Chrome is not logged in; open the bot Chrome window and sign in to Kwork once."
    return ""


def _project_unavailable_message(page_text: str) -> str:
    lowered = page_text.lower()
    unavailable_markers = (
        "страница не найдена",
        "проект не найден",
        "заказ не найден",
        "проект недоступен",
        "заказ недоступен",
        "проект закрыт",
        "заказ закрыт",
        "заказ снят",
        "page not found",
        "project not found",
        "project is unavailable",
    )
    if any(marker in lowered for marker in unavailable_markers):
        return "Kwork project is unavailable: page not found, closed, or removed."
    return ""


def _is_kwork_project_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower().endswith("kwork.ru") and re.match(r"^/projects/\d+(?:/view)?/?$", parsed.path) is not None


def _project_id(url: str) -> str:
    match = re.search(r"/projects/(\d+)", url)
    return match.group(1) if match else "unknown"


def _offer_url(url: str) -> str:
    project_id = _project_id(url)
    if project_id == "unknown":
        raise ValueError("Kwork sender requires a Kwork project URL")
    return f"https://kwork.ru/new_offer?project={project_id}"


def _offer_project_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.rstrip("/") != "/new_offer":
        return ""
    values = dict(parse_qsl(parsed.query))
    return values.get("project", "")


def _is_offer_page_for_project(url: str, project_id: str) -> bool:
    return bool(project_id) and _offer_project_id(url) == project_id


def _is_kwork_inbox_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower().endswith("kwork.ru") and parsed.path.rstrip("/").startswith("/inbox")


def _page_ids(pages: list[dict]) -> set[str]:
    return {str(page.get("id", "")) for page in pages if page.get("id")}


_OPEN_REPLY_FORM_SCRIPT = r"""
(() => {
  const norm = value => (value || '').replace(/\s+/g, ' ').trim();
  const visible = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  if (document.querySelector('.trumbowyg-editor, textarea[name="description"], #offer-custom-price')) {
    return true;
  }
  const cookie = Array.from(document.querySelectorAll('button,a')).find(el => /^(окей|ok|понятно)$/i.test(norm(el.innerText || el.value)));
  if (cookie && visible(cookie)) cookie.click();
  const opener = Array.from(document.querySelectorAll('button,a,input[type=button],input[type=submit],span.kw-button,[role=button],.kw-button')).find(el => {
    const text = norm(el.innerText || el.value || el.getAttribute('aria-label'));
    return visible(el) && /(предложить услугу|откликнуться|оставить предложение|оставить отзыв|предложить)$/i.test(text);
  });
  if (opener) opener.click();
  return true;
})()
"""

_HAS_REPLY_FIELD_SCRIPT = r"""
(() => {
  const visible = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  const norm = value => (value || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const meta = el => norm([
    el.name,
    el.id,
    el.className,
    el.placeholder,
    el.getAttribute('placeholder'),
    el.getAttribute('aria-label'),
    el.parentElement?.innerText?.slice(0, 180)
  ].filter(Boolean).join(' '));
  const textarea = document.querySelector('textarea[name="description"]');
  if (visible(textarea)) return true;
  return Array.from(document.querySelectorAll('.trumbowyg-editor,[contenteditable="true"]')).some(el => {
    return visible(el) && /(как вы будете решать|напишите|опис|description|сообщ|коммент|текст|отклик)/i.test(meta(el));
  });
})()
"""

_AUTO_LOGIN_SCRIPT = r"""
(payload) => {
  const norm = value => (value || '').replace(/\s+/g, ' ').trim();
  const visible = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  const setValue = (el, value) => {
    if (!el) return false;
    el.focus();
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (setter) setter.call(el, value); else el.value = value;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return true;
  };
  const loginOpener = Array.from(document.querySelectorAll('a,button,input[type=button]')).find(el => {
    const text = norm(el.innerText || el.value || el.getAttribute('aria-label'));
    return visible(el) && /^вход$/i.test(text);
  });
  if (loginOpener) loginOpener.click();
  const emailField = Array.from(document.querySelectorAll('input[type=email],input[name*=email i],input[name*=login i],input[type=text]'))
    .find(el => visible(el) && !el.disabled);
  const passwordField = Array.from(document.querySelectorAll('input[type=password]'))
    .find(el => visible(el) && !el.disabled);
  if (!emailField || !passwordField) {
    return JSON.stringify({started: false, reason: 'Kwork login form was not found'});
  }
  setValue(emailField, payload.email);
  setValue(passwordField, payload.password);
  const form = passwordField.closest('form') || document;
  const submit = Array.from(form.querySelectorAll('button,input[type=submit],input[type=button]')).find(el => {
    const text = norm(el.innerText || el.value || el.getAttribute('aria-label'));
    return visible(el) && /(войти|вход|login|sign in)/i.test(text);
  }) || form.querySelector('button,input[type=submit]');
  if (!submit) return JSON.stringify({started: false, reason: 'Kwork login submit button was not found'});
  submit.click();
  return JSON.stringify({started: true});
}
"""

_CONFIRM_SUBMIT_SCRIPT = r"""
(() => {
  const norm = value => (value || '').replace(/\s+/g, ' ').trim();
  const visible = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  const textOf = el => norm(el?.innerText || el?.textContent || el?.value || el?.getAttribute?.('aria-label'));
  const dialogSelector = '[role=dialog],.modal,.modal-dialog,.popup,.kw-modal,.modal-wrapper,.v--modal-box,.swal2-popup,.js-modal,.js-popup';
  const dialogs = Array.from(document.querySelectorAll(dialogSelector)).filter(visible);
  const fixedOverlays = Array.from(document.querySelectorAll('body > div')).filter(el => {
    const style = window.getComputedStyle(el);
    return visible(el) && style.position === 'fixed' && textOf(el).length > 20;
  });
  const roots = dialogs.length ? dialogs : fixedOverlays.slice(0, 6);
  for (const root of roots) {
    const rootText = textOf(root).toLowerCase();
    if (/(sms|смс|captcha|капч|верификац|подтвердите телефон|код подтверждения|код из сообщения)/i.test(rootText)) {
      return JSON.stringify({ok: false, blocked: true, reason: 'Kwork requires manual SMS/captcha/verification confirmation'});
    }
    const buttons = Array.from(root.querySelectorAll('button,input[type=button],input[type=submit],a,.kw-button,[role=button]')).filter(visible);
    const button = buttons.find(el => {
      const text = textOf(el).toLowerCase();
      if (!text || /(отмена|назад|закрыть|нет|cancel|close)/i.test(text)) return false;
      return /(подтверд|отправить|продолжить|да|ок|ok|соглас|разместить|предложить|оставить)/i.test(text);
    });
    if (button) {
      button.click();
      return JSON.stringify({ok: true, clicked: true, hasDialog: true, text: textOf(button)});
    }
  }
  return JSON.stringify({ok: true, clicked: false, hasDialog: roots.length > 0});
})()
"""

_FILL_AND_SUBMIT_SCRIPT = r"""
(payload) => {
  const norm = value => (value || '').replace(/\s+/g, ' ').trim();
  const visible = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
  const setValue = (el, value) => {
    if (!el) return false;
    el.focus();
    if (el.isContentEditable) {
      el.innerText = value;
      el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
      return true;
    }
    if (el.matches && el.matches('.trumbowyg-editor')) {
      el.classList.remove('force-placeholder', 'is-placeholder-mobile');
      const clean = value.replace(/[&<>]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[ch]));
      el.innerHTML = '<p>' + clean.replace(/\n/g, '<br>') + '</p>';
      el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
      return true;
    }
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value); else el.value = value;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return true;
  };
  const meta = el => norm([
    el.name,
    el.id,
    el.className,
    el.placeholder,
    el.getAttribute('aria-label'),
    el.closest('label')?.innerText,
    el.parentElement?.innerText?.slice(0, 160)
  ].filter(Boolean).join(' ')).toLowerCase();
  const fields = Array.from(document.querySelectorAll('textarea,.trumbowyg-editor,[contenteditable="true"],input:not([type]),input[type=text],input[type=number],input[type=tel],input[type=search]')).filter(visible);
  const messageTextarea = document.querySelector('textarea[name="description"]');
  const messageEditor = messageTextarea?.closest('.trumbowyg-box')?.querySelector('.trumbowyg-editor')
    || messageTextarea?.parentElement?.querySelector('.trumbowyg-editor')
    || Array.from(document.querySelectorAll('.trumbowyg-editor,[contenteditable="true"]')).find(el => {
      return visible(el) && /сообщ|опис|коммент|текст|message|comment|description|cover|letter|как вы будете решать/.test(meta(el));
    });
  const messageField = messageEditor
    || (messageTextarea && visible(messageTextarea) ? messageTextarea : null)
    || fields.find(el => /сообщ|опис|коммент|текст|message|comment|description|cover|letter/.test(meta(el)))
    || fields.find(el => el.matches && el.matches('.trumbowyg-editor'))
    || fields.find(el => el.tagName === 'TEXTAREA' || el.isContentEditable);
  if (!messageField) return JSON.stringify({submitted: false, reason: 'Kwork reply field was not found'});
  setValue(messageField, payload.text);
  if (messageTextarea) setValue(messageTextarea, payload.text);
  if (messageEditor && messageEditor !== messageField) setValue(messageEditor, payload.text);
  const priceField = document.querySelector('#offer-custom-price') || fields.find(el => /цен|стоим|бюдж|price|cost|amount|budget|sum/.test(meta(el)));
  if (priceField && payload.price) setValue(priceField, payload.price);
  const titleTextarea = document.querySelector('textarea[name="name"][placeholder="Введите название заказа"], textarea[name="name"]');
  const titleEditor = titleTextarea?.closest('.trumbowyg-box')?.querySelector('.trumbowyg-editor')
    || titleTextarea?.parentElement?.querySelector('.trumbowyg-editor');
  const titleField = titleEditor || titleTextarea || Array.from(document.querySelectorAll('input[type=text],input:not([type]),textarea')).find(el => {
    const text = meta(el);
    return visible(el) && (/название заказа|order title|project title/.test(text) || el.placeholder === 'Введите название заказа');
  });
  if (titleField && payload.title) setValue(titleField, payload.title.slice(0, 70));
  if (titleTextarea && payload.title) setValue(titleTextarea, payload.title.slice(0, 70));
  const daysField = fields.find(el => /срок|дн|day|days|duration|deadline/.test(meta(el))) || document.querySelector('input[placeholder="Срок выполнения"], input.vs__search');
  if (daysField && payload.days) setValue(daysField, payload.days);
  if (!payload.submit) {
    return JSON.stringify({
      ok: true,
      submitted: false,
      priceFilled: Boolean(priceField && payload.price),
      titleFilled: Boolean(titleField && payload.title),
      daysFilled: Boolean(daysField && payload.days)
    });
  }
  const form = messageField.closest('form') || document;
  const buttons = Array.from(form.querySelectorAll('button,input[type=submit],input[type=button],a')).filter(visible);
  const submit = buttons.find(el => /отправить|предложить|оставить предложение|разместить|подать/i.test(norm(el.innerText || el.value || el.getAttribute('aria-label'))));
  if (!submit) return JSON.stringify({ok: false, submitted: false, reason: 'Kwork submit button was not found'});
  submit.click();
  return JSON.stringify({
    ok: true,
    submitted: true,
    priceFilled: Boolean(priceField && payload.price),
    titleFilled: Boolean(titleField && payload.title),
    daysFilled: Boolean(daysField && payload.days)
  });
}
"""
