from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, Button, Entry, Label, LabelFrame, StringVar, Text, Tk, messagebox, scrolledtext
from tkinter import ttk

from app.config import load_config
from app.kwork_sender import KworkReplySender, _extract_reply_terms
from app.storage import Lead, Storage


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

FILTER_SETTINGS = (
    ("KWORK_MAX_RESPONSES", "Макс. откликов в заказе", "5"),
    ("SCAN_INTERVAL_SECONDS", "Интервал мониторинга, сек", "60"),
    ("MAX_POSTS_PER_CHANNEL", "Заказов за проход", "30"),
    ("LEAD_MIN_SCORE", "Мин. AI score", "60"),
    ("LEAD_MAX_DAYS", "Макс. срок, дней", "7"),
    ("LEAD_ACCEPT_DECISIONS", "AI решения принимать", "accept, maybe"),
    ("LEAD_BLOCKED_KEYWORDS", "Стоп-слова", "битрикс, bitrix"),
    (
        "LEAD_HARD_REJECT_KEYWORDS",
        "Сложные/чужие стеки",
        "1c, 1с, android, ios, flutter, react native, мобильное приложение, devops, kubernetes, blockchain, crypto, крипто, сложная crm, erp",
    ),
    ("LEAD_REQUIRED_KEYWORDS", "Обязательные слова (можно пусто)", ""),
    ("KWORK_PROJECTS_URL", "Страница Kwork", "https://kwork.ru/projects?c=11"),
)

INTEGER_LIMITS = {
    "KWORK_MAX_RESPONSES": (0, 100),
    "SCAN_INTERVAL_SECONDS": (10, 3600),
    "MAX_POSTS_PER_CHANNEL": (1, 200),
    "LEAD_MIN_SCORE": (0, 100),
    "LEAD_MAX_DAYS": (1, 30),
}


def build_app_command(command: str, root_dir: Path = ROOT_DIR) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir / "src")
    return [sys.executable, "-m", "app.main", command], env


def build_script_command(script_path: Path) -> list[str]:
    return ["cmd", "/c", str(script_path)]


class LeadFunnelGui:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Kwork Lead Funnel")
        self.root.geometry("980x760")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.watch_process: subprocess.Popen[str] | None = None
        self.setting_vars: dict[str, StringVar] = {}
        self.current_lead_id: int | None = None
        self.lead_rows: dict[str, int] = {}

        self.status = Label(root, text="Готово", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(10, 4))

        self._create_settings_panel()
        self._create_leads_panel()

        self.start_browser_button = Button(root, text="1. Открыть Kwork Chrome", command=self.start_kwork_browser)
        self.start_browser_button.pack(fill="x", padx=10, pady=3)

        self.scan_button = Button(root, text="2. Сканировать сейчас", command=self.scan_once)
        self.scan_button.pack(fill="x", padx=10, pady=3)

        self.start_watch_button = Button(root, text="3. Старт мониторинга", command=self.start_watch)
        self.start_watch_button.pack(fill="x", padx=10, pady=3)

        self.approvals_button = Button(root, text="4. Проверить OK и отправить отклики", command=self.process_approvals)
        self.approvals_button.pack(fill="x", padx=10, pady=3)

        self.stop_watch_button = Button(root, text="Стоп мониторинга", command=self.stop_watch, state=DISABLED)
        self.stop_watch_button.pack(fill="x", padx=10, pady=3)

        self.clear_button = Button(root, text="Очистить лог", command=self.clear_log)
        self.clear_button.pack(fill="x", padx=10, pady=3)

        self.log = scrolledtext.ScrolledText(root, wrap="word", height=10)
        self.log.pack(fill=BOTH, expand=True, padx=10, pady=(8, 10))
        self.write_log("Открой Kwork Chrome, войди в Kwork один раз, затем запускай сканирование или мониторинг.\n")
        self.write_log(self._filter_summary())
        self.refresh_leads()

    def _create_settings_panel(self) -> None:
        frame = LabelFrame(self.root, text="Настройки отбора")
        frame.pack(fill="x", padx=10, pady=(4, 8))
        values = read_env_values(ENV_PATH)

        for row, (key, label, default) in enumerate(FILTER_SETTINGS):
            Label(frame, text=label, anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=3)
            variable = StringVar(value=values.get(key, default))
            self.setting_vars[key] = variable
            Entry(frame, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=8, pady=3)

        frame.columnconfigure(1, weight=1)
        button_row = len(FILTER_SETTINGS)
        Button(frame, text="Сохранить настройки", command=self.save_settings).grid(
            row=button_row,
            column=0,
            sticky="ew",
            padx=8,
            pady=(8, 6),
        )
        Button(frame, text="Перезагрузить из .env", command=self.reload_settings).grid(
            row=button_row,
            column=1,
            sticky="ew",
            padx=8,
            pady=(8, 6),
        )

    def _create_leads_panel(self) -> None:
        frame = LabelFrame(self.root, text="Лиды и отклик")
        frame.pack(fill="both", padx=10, pady=(0, 8))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="x", padx=8, pady=(8, 4))
        columns = ("id", "status", "score", "price", "days", "title")
        self.leads_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        headings = {
            "id": "ID",
            "status": "Статус",
            "score": "Score",
            "price": "Цена",
            "days": "Дн.",
            "title": "Задача",
        }
        widths = {"id": 50, "status": 90, "score": 60, "price": 80, "days": 55, "title": 620}
        for column in columns:
            self.leads_table.heading(column, text=headings[column])
            self.leads_table.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.leads_table.yview)
        self.leads_table.configure(yscrollcommand=scrollbar.set)
        self.leads_table.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.leads_table.bind("<<TreeviewSelect>>", self.on_lead_select)

        fields = ttk.Frame(frame)
        fields.pack(fill="x", padx=8, pady=4)
        self.lead_title_var = StringVar()
        self.lead_price_var = StringVar()
        self.lead_days_var = StringVar()
        self.lead_status_var = StringVar(value="Лид не выбран")

        Label(fields, text="Название").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        Entry(fields, textvariable=self.lead_title_var).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
        Label(fields, text="Цена").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)
        Entry(fields, textvariable=self.lead_price_var, width=10).grid(row=0, column=3, sticky="w", padx=(0, 8), pady=2)
        Label(fields, text="Срок, дней").grid(row=0, column=4, sticky="w", padx=(0, 6), pady=2)
        Entry(fields, textvariable=self.lead_days_var, width=8).grid(row=0, column=5, sticky="w", pady=2)
        Label(fields, textvariable=self.lead_status_var, anchor="w").grid(row=1, column=0, columnspan=6, sticky="ew", pady=2)
        fields.columnconfigure(1, weight=1)

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.summary_text = Text(text_frame, height=5, wrap="word")
        self.summary_text.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.reply_text = Text(text_frame, height=5, wrap="word")
        self.reply_text.pack(side="left", fill="both", expand=True, padx=(6, 0))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", padx=8, pady=(4, 8))
        Button(buttons, text="Обновить лиды", command=self.refresh_leads).pack(side="left", padx=(0, 6))
        Button(buttons, text="Сохранить правки", command=self.save_lead_edits).pack(side="left", padx=6)
        Button(buttons, text="Открыть заказ", command=self.open_selected_lead).pack(side="left", padx=6)
        Button(buttons, text="Заполнить в Kwork", command=self.prepare_selected_lead).pack(side="left", padx=6)
        Button(buttons, text="Отправить отклик", command=self.send_selected_lead).pack(side="left", padx=6)

    def start_kwork_browser(self) -> None:
        script = ROOT_DIR / "start-kwork-browser.cmd"
        self._run_once(build_script_command(script), os.environ.copy(), "Kwork Chrome")

    def scan_once(self) -> None:
        command, env = build_app_command("scan")
        self._run_once(command, env, "Сканирование")

    def process_approvals(self) -> None:
        command, env = build_app_command("approvals")
        self._run_once(command, env, "Проверка OK")

    def refresh_leads(self) -> None:
        try:
            storage = self._storage()
            leads = storage.list_leads()
        except Exception as exc:
            self.write_log(f"Не удалось загрузить лиды: {exc}\n")
            return
        self.lead_rows.clear()
        self.leads_table.delete(*self.leads_table.get_children())
        for lead in reversed(leads[-80:]):
            price = _extract_price(lead)
            days = _extract_days(lead)
            title = _lead_title(lead)
            item_id = self.leads_table.insert(
                "",
                END,
                values=(lead.id, lead.status, lead.score, price or "", days or "", title),
            )
            self.lead_rows[item_id] = lead.id

    def on_lead_select(self, _event=None) -> None:
        selected = self.leads_table.selection()
        if not selected:
            return
        lead_id = self.lead_rows.get(selected[0])
        if lead_id is None:
            return
        try:
            lead = self._storage().get_lead(lead_id)
        except Exception as exc:
            self.write_log(f"Не удалось открыть лид #{lead_id}: {exc}\n")
            return
        self.current_lead_id = lead.id
        self.lead_title_var.set(_lead_title(lead))
        self.lead_price_var.set(str(_extract_price(lead) or ""))
        self.lead_days_var.set(str(_extract_days(lead) or ""))
        status = f"Лид #{lead.id}: {lead.status}; ссылка: {lead.post_url}"
        if lead.last_error:
            status += f"; ошибка: {lead.last_error}"
        self.lead_status_var.set(status)
        self.summary_text.delete("1.0", END)
        self.summary_text.insert("1.0", lead.summary)
        self.reply_text.delete("1.0", END)
        self.reply_text.insert("1.0", lead.draft_reply)

    def save_lead_edits(self) -> None:
        lead_id = self._selected_lead_id()
        if lead_id is None:
            return
        reply = self.reply_text.get("1.0", END).strip()
        try:
            self._storage().update_lead_reply(lead_id, reply)
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.write_log(f"Лид #{lead_id}: текст отклика сохранен.\n")
        self.refresh_leads()

    def open_selected_lead(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        self._run_lead_action("Открытие заказа", lambda: self._open_kwork_lead(lead), lead_id=lead.id)

    def prepare_selected_lead(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        self._save_selected_reply_if_changed(lead.id)
        try:
            payload = self._lead_payload(lead)
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self._run_lead_action(
            f"Заполнение лида #{lead.id}",
            lambda: self._sender().prepare_reply(
                lead.contact,
                payload["reply"],
                price_rub=payload["price"],
                days=payload["days"],
                title=payload["title"],
            ),
            lead_id=lead.id,
        )

    def send_selected_lead(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        if not messagebox.askyesno("Отправить отклик", f"Реально отправить отклик по лиду #{lead.id}?"):
            return
        self._save_selected_reply_if_changed(lead.id)
        try:
            payload = self._lead_payload(lead)
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self._run_lead_action(
            f"Отправка лида #{lead.id}",
            lambda: self._send_lead_now(lead, payload),
            lead_id=lead.id,
        )

    def _send_lead_now(self, lead: Lead, payload: dict) -> str:
        message_id = self._sender().send_reply(
            lead.contact,
            payload["reply"],
            price_rub=payload["price"],
            days=payload["days"],
            title=payload["title"],
            submit=True,
        )
        self._storage().mark_sent(lead.id, lead.contact, message_id)
        return message_id

    def _run_lead_action(self, label: str, action, lead_id: int | None = None) -> None:
        self.status.config(text=f"{label}: выполняется")
        self.write_log(f"=== {label}: старт ===\n")
        threading.Thread(target=self._run_lead_action_thread, args=(label, action, lead_id), daemon=True).start()

    def _run_lead_action_thread(self, label: str, action, lead_id: int | None) -> None:
        try:
            result = action()
        except Exception as exc:
            if lead_id is not None:
                try:
                    self._storage().mark_failed(lead_id, str(exc))
                except Exception:
                    pass
            self.write_log(f"=== {label}: ошибка: {exc} ===\n")
            self.root.after(0, lambda: self.status.config(text=f"{label}: ошибка"))
        else:
            self.write_log(f"=== {label}: готово ({result}) ===\n")
            self.root.after(0, lambda: self.status.config(text=f"{label}: готово"))
        finally:
            self.root.after(0, self.refresh_leads)

    def _lead_payload(self, lead: Lead) -> dict:
        reply = self.reply_text.get("1.0", END).strip()
        if not reply:
            raise ValueError("Текст отклика пустой")
        return {
            "reply": reply,
            "title": self.lead_title_var.get().strip() or _lead_title(lead),
            "price": _parse_optional_int(self.lead_price_var.get(), "Цена"),
            "days": _parse_optional_int(self.lead_days_var.get(), "Срок"),
        }

    def _save_selected_reply_if_changed(self, lead_id: int) -> None:
        reply = self.reply_text.get("1.0", END).strip()
        if reply:
            self._storage().update_lead_reply(lead_id, reply)

    def _selected_lead_id(self) -> int | None:
        selected = self.leads_table.selection()
        if not selected:
            messagebox.showwarning("Лид не выбран", "Выбери лид в таблице.")
            return None
        return self.lead_rows.get(selected[0])

    def _selected_lead(self) -> Lead | None:
        lead_id = self._selected_lead_id()
        if lead_id is None:
            return None
        return self._storage().get_lead(lead_id)

    def _storage(self) -> Storage:
        config = load_config()
        storage = Storage(config.database_path)
        storage.initialize()
        return storage

    def _sender(self) -> KworkReplySender:
        config = load_config()
        return KworkReplySender(
            timeout_seconds=45,
            cdp_url=config.kwork_cdp_url,
            browser_profile_dir=config.kwork_browser_profile_dir,
            login_email=config.kwork_login_email,
            login_password=config.kwork_login_password,
        )

    def _open_kwork_lead(self, lead: Lead) -> str:
        from app import kwork_source

        config = load_config()
        kwork_source._ensure_chrome_cdp(config.kwork_cdp_url, lead.contact, config.kwork_browser_profile_dir)
        version = kwork_source._cdp_json(config.kwork_cdp_url, "/json/version", timeout=5)
        if not version:
            raise RuntimeError("Chrome DevTools недоступен")
        import websocket

        ws = websocket.create_connection(version["webSocketDebuggerUrl"], timeout=10)
        try:
            kwork_source._send_cdp(ws, "Target.createTarget", {"url": lead.contact})
        finally:
            ws.close()
        return f"opened lead {lead.id}"

    def start_watch(self) -> None:
        if self.watch_process and self.watch_process.poll() is None:
            self.write_log("Мониторинг уже запущен.\n")
            return
        command, env = build_app_command("watch")
        self.watch_process = subprocess.Popen(
            command,
            cwd=ROOT_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.status.config(text="Мониторинг запущен")
        self.start_watch_button.config(state=DISABLED)
        self.stop_watch_button.config(state=NORMAL)
        self.write_log("=== Мониторинг запущен ===\n")
        threading.Thread(target=self._stream_process, args=(self.watch_process, "Мониторинг"), daemon=True).start()

    def stop_watch(self) -> None:
        if not self.watch_process or self.watch_process.poll() is not None:
            self.status.config(text="Мониторинг не запущен")
            self.start_watch_button.config(state=NORMAL)
            self.stop_watch_button.config(state=DISABLED)
            return
        self.watch_process.terminate()
        try:
            self.watch_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.watch_process.kill()
        self.status.config(text="Мониторинг остановлен")
        self.start_watch_button.config(state=NORMAL)
        self.stop_watch_button.config(state=DISABLED)
        self.write_log("=== Мониторинг остановлен ===\n")

    def clear_log(self) -> None:
        self.log.delete("1.0", END)

    def save_settings(self) -> None:
        try:
            updates = normalize_filter_settings({key: var.get() for key, var in self.setting_vars.items()})
        except ValueError as exc:
            messagebox.showerror("Ошибка настроек", str(exc))
            return
        update_env_values(ENV_PATH, updates)
        for key, value in updates.items():
            self.setting_vars[key].set(value)
        self.write_log("Настройки сохранены в .env. Если мониторинг уже запущен, перезапусти его.\n")
        self.write_log(self._filter_summary())

    def reload_settings(self) -> None:
        values = read_env_values(ENV_PATH)
        defaults = {key: default for key, _, default in FILTER_SETTINGS}
        for key, variable in self.setting_vars.items():
            variable.set(values.get(key, defaults.get(key, "")))
        self.write_log("Настройки перечитаны из .env.\n")

    def _filter_summary(self) -> str:
        values = {key: var.get() for key, var in self.setting_vars.items()}
        return (
            "Текущий отбор: "
            f"откликов <= {values.get('KWORK_MAX_RESPONSES', '5')}, "
            f"AI score >= {values.get('LEAD_MIN_SCORE', '60')}, "
            f"срок <= {values.get('LEAD_MAX_DAYS', '7')} дн., "
            f"решения: {values.get('LEAD_ACCEPT_DECISIONS', 'accept, maybe')}, "
            f"стоп-слова: {values.get('LEAD_BLOCKED_KEYWORDS', 'битрикс, bitrix')}.\n"
        )

    def close(self) -> None:
        self.stop_watch()
        self.root.destroy()

    def _run_once(self, command: list[str], env: dict[str, str], label: str) -> None:
        self.status.config(text=f"{label}: выполняется")
        self.write_log(f"=== {label}: старт ===\n")
        threading.Thread(target=self._run_once_thread, args=(command, env, label), daemon=True).start()

    def _run_once_thread(self, command: list[str], env: dict[str, str], label: str) -> None:
        process = subprocess.Popen(
            command,
            cwd=ROOT_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self._stream_process(process, label)
        self.root.after(0, lambda: self.status.config(text=f"{label}: завершено"))
        self.write_log(f"=== {label}: завершено с кодом {process.returncode} ===\n")

    def _stream_process(self, process: subprocess.Popen[str], label: str) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            self.write_log(line)
        process.wait()
        if process is self.watch_process:
            self.root.after(0, lambda: self.start_watch_button.config(state=NORMAL))
            self.root.after(0, lambda: self.stop_watch_button.config(state=DISABLED))
            self.root.after(0, lambda: self.status.config(text=f"{label}: остановлен"))

    def write_log(self, text: str) -> None:
        self.root.after(0, lambda: self._append_log(text))

    def _append_log(self, text: str) -> None:
        self.log.insert(END, text)
        self.log.see(END)


def main() -> int:
    root = Tk()
    LeadFunnelGui(root)
    root.mainloop()
    return 0


def read_env_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def update_env_values(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    result: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            result.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            result.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            result.append(line)

    for key, value in updates.items():
        if key not in seen:
            result.append(f"{key}={value}")

    path.write_text("\n".join(result).rstrip() + "\n", encoding="utf-8")


def normalize_filter_settings(values: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in values.items():
        value = value.strip()
        if key in INTEGER_LIMITS:
            normalized[key] = _normalize_int_setting(key, value)
        elif key == "LEAD_ACCEPT_DECISIONS":
            normalized[key] = _normalize_decisions(value)
        elif key == "KWORK_PROJECTS_URL":
            if not value.startswith("https://kwork.ru/"):
                raise ValueError("Страница Kwork должна начинаться с https://kwork.ru/")
            normalized[key] = value
        else:
            normalized[key] = _normalize_csv(value)
    return normalized


def _normalize_int_setting(key: str, value: str) -> str:
    minimum, maximum = INTEGER_LIMITS[key]
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{key}: нужно целое число") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{key}: допустимо от {minimum} до {maximum}")
    return str(number)


def _normalize_decisions(value: str) -> str:
    allowed = {"accept", "maybe", "reject"}
    decisions = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not decisions:
        raise ValueError("LEAD_ACCEPT_DECISIONS: укажи accept, maybe или reject")
    invalid = [item for item in decisions if item not in allowed]
    if invalid:
        raise ValueError(f"LEAD_ACCEPT_DECISIONS: неизвестные значения: {', '.join(invalid)}")
    return ", ".join(dict.fromkeys(decisions))


def _normalize_csv(value: str) -> str:
    return ", ".join(item.strip() for item in value.split(",") if item.strip())


def _extract_price(lead: Lead) -> int | None:
    terms = _extract_reply_terms(lead.draft_reply)
    if terms.price_rub is not None:
        return terms.price_rub
    import re

    match = re.search(r"Цена:\s*(\d[\d\s]*)\s*руб", lead.summary, re.IGNORECASE)
    return int(match.group(1).replace(" ", "")) if match else None


def _extract_days(lead: Lead) -> int | None:
    terms = _extract_reply_terms(lead.draft_reply)
    if terms.days is not None:
        return terms.days
    import re

    match = re.search(r"Срок:\s*(\d{1,2})\s*дн", lead.summary, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _lead_title(lead: Lead) -> str:
    for line in lead.summary.splitlines():
        clean = line.strip()
        if clean.startswith("Задача:"):
            return clean.removeprefix("Задача:").strip()[:70]
    first_line = next((line.strip() for line in lead.summary.splitlines() if line.strip()), "")
    return (first_line or f"Kwork lead {lead.id}")[:70]


def _parse_optional_int(value: str, label: str) -> int | None:
    clean = value.strip().replace(" ", "")
    if not clean:
        return None
    try:
        number = int(clean)
    except ValueError as exc:
        raise ValueError(f"{label}: нужно число") from exc
    if number <= 0:
        raise ValueError(f"{label}: число должно быть больше 0")
    return number


if __name__ == "__main__":
    raise SystemExit(main())
