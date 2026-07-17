from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, StringVar, TclError, Tk, messagebox, scrolledtext
from tkinter import ttk

from app.ai_lead_judge import sanitize_customer_reply
from app.config import load_config
from app.kwork_sender import KworkReplySender, _extract_reply_terms
from app.reply_composer import (
    ReplyDraftContext,
    compose_customer_reply,
    reply_delivery_issue_labels,
    reply_delivery_issue_summary,
)
from app.storage import Lead, LeadAttachment, PostRejection, Storage


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
MOSCOW_TZ = timezone(timedelta(hours=3), "МСК")
WATCH_REFRESH_MS = 5000
REFRESH_AFTER_LABELS = {"Сканирование", "Проверка почты"}

FILTER_SETTINGS = (
    ("KWORK_MAX_RESPONSES", "Макс. откликов в заказе", "5"),
    ("KWORK_MAX_AGE_HOURS", "Возраст заказа, часов (0 = без лимита)", "24"),
    ("SCAN_INTERVAL_SECONDS", "Интервал мониторинга, сек", "60"),
    ("MAX_POSTS_PER_CHANNEL", "Заказов за проход", "30"),
    ("LEAD_MIN_SCORE", "Мин. AI score", "60"),
    ("LEAD_MAX_DAYS", "Макс. срок, дней", "7"),
    ("LEAD_ACCEPT_DECISIONS", "AI решения принимать", "accept, maybe"),
    ("LEAD_BLOCKED_KEYWORDS", "Стоп-слова", "битрикс, bitrix"),
    (
        "LEAD_HARD_REJECT_KEYWORDS",
        "Доп. жёсткие стоп-слова (можно пусто)",
        "",
    ),
    ("LEAD_REQUIRED_KEYWORDS", "Обязательные слова (можно пусто)", ""),
    ("KWORK_PROJECTS_URL", "Страница Kwork", "https://kwork.ru/projects?c=11"),
)

INTEGER_LIMITS = {
    "KWORK_MAX_RESPONSES": (0, 100),
    "KWORK_MAX_AGE_HOURS": (0, 720),
    "SCAN_INTERVAL_SECONDS": (10, 3600),
    "MAX_POSTS_PER_CHANNEL": (1, 200),
    "LEAD_MIN_SCORE": (0, 100),
    "LEAD_MAX_DAYS": (1, 30),
}

COLORS = {
    "bg": "#f5f7fb",
    "panel": "#ffffff",
    "panel_alt": "#eef3f8",
    "text": "#182230",
    "muted": "#667085",
    "line": "#d8dee8",
    "accent": "#0f766e",
    "accent_hover": "#115e59",
    "danger": "#b42318",
    "danger_hover": "#912018",
}


def build_app_command(command: str, root_dir: Path = ROOT_DIR) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    return [sys.executable, "-m", "app.main", command], env


def build_script_command(script_path: Path) -> list[str]:
    return ["cmd", "/c", str(script_path)]


class LeadFunnelGui:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Kwork Lead Funnel")
        self.root.geometry("1180x820")
        self.root.minsize(1040, 720)
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.watch_process: subprocess.Popen[str] | None = None
        self.watch_refresh_after_id: str | None = None
        self.setting_vars: dict[str, StringVar] = {}
        self.current_lead_id: int | None = None
        self.lead_rows: dict[str, int] = {}
        self.attachment_rows: dict[str, LeadAttachment] = {}
        self.rejection_rows: dict[str, PostRejection] = {}
        self.in_flight_lead_ids: set[int] = set()
        self.running_once_actions: set[str] = set()
        self.once_action_buttons: dict[str, ttk.Button] = {}
        self.pending_replies: dict[int, str] = {}
        self.lead_action_errors: dict[int, str] = {}
        self.kwork_price_limits: dict[int, int] = {}
        self.reply_regeneration_in_flight = False
        self.status_var = StringVar(value="Готово")

        self._configure_style()

        app = ttk.Frame(root, style="App.TFrame", padding=16)
        app.pack(fill=BOTH, expand=True)

        self._create_header(app)
        self._create_action_bar(app)

        self.notebook = ttk.Notebook(app, style="Modern.TNotebook")
        self.notebook.pack(fill=BOTH, expand=True, pady=(12, 0))

        self.leads_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=14)
        self.rejections_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=14)
        self.settings_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=14)
        self.log_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=14)
        self.notebook.add(self.leads_tab, text="Лиды")
        self.notebook.add(self.rejections_tab, text="Отсев")
        self.notebook.add(self.settings_tab, text="Настройки")
        self.notebook.add(self.log_tab, text="Лог")

        self._create_leads_panel(self.leads_tab)
        self._create_rejections_panel(self.rejections_tab)
        self._create_settings_panel(self.settings_tab)
        self._create_log_panel(self.log_tab)
        self.write_log("Открой Kwork Chrome, войди в Kwork один раз, затем запускай сканирование или мониторинг.\n")
        self.write_log(self._filter_summary())
        self.refresh_leads()

    def _configure_style(self) -> None:
        self.root.option_add("*Font", ("Segoe UI", 10))
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background=COLORS["panel"])
        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Card.TFrame", background=COLORS["panel"], relief="flat")
        style.configure("Header.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI Semibold", 19))
        style.configure("Subtle.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"])
        style.configure("Status.TLabel", background=COLORS["panel_alt"], foreground=COLORS["accent"], padding=(12, 6), font=("Segoe UI Semibold", 10))
        style.configure("Link.TLabel", background=COLORS["panel"], foreground="#2563eb", font=("Segoe UI", 10, "underline"))
        style.configure("Modern.TButton", padding=(12, 8), background=COLORS["panel"], foreground=COLORS["text"], bordercolor=COLORS["line"])
        style.map("Modern.TButton", background=[("active", COLORS["panel_alt"])])
        style.configure("Accent.TButton", padding=(13, 8), background=COLORS["accent"], foreground="#ffffff", bordercolor=COLORS["accent"])
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("disabled", COLORS["line"])], foreground=[("disabled", COLORS["muted"])])
        style.configure("Danger.TButton", padding=(12, 8), background=COLORS["danger"], foreground="#ffffff", bordercolor=COLORS["danger"])
        style.map("Danger.TButton", background=[("active", COLORS["danger_hover"]), ("disabled", COLORS["line"])], foreground=[("disabled", COLORS["muted"])])
        style.configure("Modern.TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("Modern.TNotebook.Tab", padding=(18, 9), background=COLORS["panel_alt"], foreground=COLORS["muted"])
        style.map("Modern.TNotebook.Tab", background=[("selected", COLORS["panel"])], foreground=[("selected", COLORS["text"])])
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background="#ffffff", fieldbackground="#ffffff", foreground=COLORS["text"], borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background=COLORS["panel_alt"], foreground=COLORS["muted"], relief="flat")
        style.map("Treeview", background=[("selected", "#d9f0ec")], foreground=[("selected", COLORS["text"])])
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor=COLORS["line"], padding=6)

    def _create_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="App.TFrame")
        header.pack(fill="x")
        title_block = ttk.Frame(header, style="App.TFrame")
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="Kwork Lead Funnel", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            title_block,
            text="Поиск заказов, проверка ТЗ и аккуратный отклик без лишней суеты.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(3, 0))
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").pack(side="right", anchor="ne")

    def _create_action_bar(self, parent: ttk.Frame) -> None:
        bar = ttk.Frame(parent, style="App.TFrame")
        bar.pack(fill="x", pady=(14, 0))
        self.start_browser_button = ttk.Button(bar, text="Открыть Kwork Chrome", command=self.start_kwork_browser, style="Modern.TButton")
        self.start_browser_button.pack(side="left", padx=(0, 8))
        self.scan_button = ttk.Button(bar, text="Сканировать", command=self.scan_once, style="Accent.TButton")
        self.scan_button.pack(side="left", padx=8)
        self.start_watch_button = ttk.Button(bar, text="Старт мониторинга", command=self.start_watch, style="Modern.TButton")
        self.start_watch_button.pack(side="left", padx=8)
        self.stop_watch_button = ttk.Button(bar, text="Стоп", command=self.stop_watch, state=DISABLED, style="Danger.TButton")
        self.stop_watch_button.pack(side="left", padx=8)
        self.approvals_button = ttk.Button(bar, text="Проверить почту", command=self.process_approvals, style="Modern.TButton")
        self.approvals_button.pack(side="left", padx=8)
        self.once_action_buttons.update(
            {
                "Kwork Chrome": self.start_browser_button,
                "Сканирование": self.scan_button,
                "Проверка почты": self.approvals_button,
            }
        )
        self.clear_button = ttk.Button(bar, text="Очистить лог", command=self.clear_log, style="Modern.TButton")
        self.clear_button.pack(side="right")

    def _create_settings_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill="x")
        ttk.Label(frame, text="Настройки отбора", style="Panel.TLabel", font=("Segoe UI Semibold", 14)).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 10),
        )
        values = read_env_values(ENV_PATH)

        for row, (key, label, default) in enumerate(FILTER_SETTINGS):
            grid_row = row + 1
            ttk.Label(frame, text=label, style="Panel.TLabel").grid(row=grid_row, column=0, sticky="w", padx=(0, 12), pady=5)
            variable = StringVar(value=values.get(key, default))
            self.setting_vars[key] = variable
            ttk.Entry(frame, textvariable=variable).grid(row=grid_row, column=1, sticky="ew", pady=5)

        frame.columnconfigure(1, weight=1)
        button_row = len(FILTER_SETTINGS) + 1
        ttk.Button(frame, text="Сохранить настройки", command=self.save_settings, style="Accent.TButton").grid(
            row=button_row,
            column=0,
            sticky="ew",
            padx=(0, 8),
            pady=(12, 0),
        )
        ttk.Button(frame, text="Перезагрузить из .env", command=self.reload_settings, style="Modern.TButton").grid(
            row=button_row,
            column=1,
            sticky="ew",
            pady=(12, 0),
        )

    def _create_leads_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=BOTH, expand=True)
        ttk.Label(frame, text="Лиды", style="Panel.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        ttk.Label(frame, text="Выбери лид, поправь цену, срок и текст, затем заполни или отправь отклик.", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="x", pady=(0, 8))
        columns = ("id", "posted", "offers", "sent", "status", "score", "price", "days", "title")
        self.leads_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=9)
        headings = {
            "id": "ID",
            "posted": "Дата",
            "offers": "Откл.",
            "sent": "Наш отклик",
            "status": "Статус",
            "score": "Score",
            "price": "Цена",
            "days": "Дн.",
            "title": "Название заказа",
        }
        widths = {
            "id": 48,
            "posted": 92,
            "offers": 58,
            "sent": 132,
            "status": 82,
            "score": 58,
            "price": 76,
            "days": 48,
            "title": 520,
        }
        for column in columns:
            self.leads_table.heading(column, text=headings[column])
            self.leads_table.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.leads_table.yview)
        self.leads_table.configure(yscrollcommand=scrollbar.set)
        self.leads_table.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.leads_table.bind("<<TreeviewSelect>>", self.on_lead_select)
        self.leads_table.tag_configure("new", background="#fffbeb")
        self.leads_table.tag_configure("emailed", background="#f8fafc")
        self.leads_table.tag_configure("failed", background="#fff1f0")
        self.leads_table.tag_configure("sent", background="#ecfdf3")
        self.leads_table.tag_configure("low_score", background="#fff7ed")

        fields = ttk.Frame(frame)
        fields.pack(fill="x", pady=(6, 4))
        self.lead_title_var = StringVar()
        self.lead_price_var = StringVar()
        self.lead_days_var = StringVar()
        self.lead_status_var = StringVar(value="Лид не выбран")
        self.lead_url_var = StringVar()

        ttk.Label(fields, text="Название", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(fields, textvariable=self.lead_title_var).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
        ttk.Label(fields, text="Цена", style="Panel.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(fields, textvariable=self.lead_price_var, width=10).grid(row=0, column=3, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(fields, text="Срок", style="Panel.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(fields, textvariable=self.lead_days_var, width=8).grid(row=0, column=5, sticky="w", pady=2)
        ttk.Label(fields, text="Ссылка", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.lead_url_label = ttk.Label(
            fields,
            textvariable=self.lead_url_var,
            style="Link.TLabel",
            cursor="hand2",
            anchor="w",
        )
        self.lead_url_label.grid(row=1, column=1, columnspan=5, sticky="ew", pady=2)
        self.lead_url_label.bind("<Button-1>", self.open_selected_lead_from_url)
        ttk.Label(fields, textvariable=self.lead_status_var, style="Muted.TLabel", anchor="w").grid(row=2, column=0, columnspan=6, sticky="ew", pady=2)
        fields.columnconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(4, 6))
        ttk.Button(buttons, text="Обновить", command=self.refresh_leads, style="Modern.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Сохранить", command=self.save_lead_edits, style="Modern.TButton").pack(side="left", padx=6)
        self.regenerate_reply_button = ttk.Button(
            buttons,
            text="Пересобрать отклик",
            command=self.regenerate_selected_reply,
            style="Accent.TButton",
        )
        self.regenerate_reply_button.pack(side="left", padx=6)
        self.apply_kwork_price_button = ttk.Button(
            buttons,
            text="Применить максимум Kwork",
            command=self.apply_kwork_price_limit,
            state=DISABLED,
            style="Modern.TButton",
        )
        self.apply_kwork_price_button.pack(side="left", padx=6)
        ttk.Button(buttons, text="Открыть заказ", command=self.open_selected_lead, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(buttons, text="Скопировать ссылку", command=self.copy_selected_lead_url, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(buttons, text="Заполнить в Kwork", command=self.prepare_selected_lead, style="Accent.TButton").pack(side="left", padx=6)
        self.send_lead_button = ttk.Button(
            buttons,
            text="OK и отправить отклик",
            command=self.send_selected_lead,
            style="Danger.TButton",
        )
        self.send_lead_button.pack(side="right")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True, pady=6)
        ttk.Label(text_frame, text="Данные заказа и AI-оценка", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Label(text_frame, text="Текст отклика", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.summary_text = scrolledtext.ScrolledText(text_frame, height=7, wrap="word", bg="#f8fafc", fg=COLORS["text"], relief="flat", padx=10, pady=10, font=("Segoe UI", 10))
        self.summary_text.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(4, 0))
        self.reply_text = scrolledtext.ScrolledText(text_frame, height=7, wrap="word", bg="#ffffff", fg=COLORS["text"], insertbackground=COLORS["accent"], relief="solid", bd=1, padx=10, pady=10, font=("Segoe UI", 10))
        self.reply_text.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(4, 0))
        self._bind_copyable_text(self.summary_text)
        self._bind_copyable_text(self.reply_text)
        text_frame.columnconfigure(0, weight=1)
        text_frame.columnconfigure(1, weight=1)
        text_frame.rowconfigure(1, weight=1)

        attachments_frame = ttk.Frame(frame)
        attachments_frame.pack(fill="x", pady=(2, 6))
        ttk.Label(attachments_frame, text="Вложения и отработка", style="Muted.TLabel").pack(anchor="w")
        attachment_table_frame = ttk.Frame(attachments_frame)
        attachment_table_frame.pack(fill="x", pady=(4, 0))
        attachment_columns = ("label", "status", "kind", "local", "summary")
        self.attachments_table = ttk.Treeview(attachment_table_frame, columns=attachment_columns, show="headings", height=4)
        attachment_headings = {
            "label": "Файл",
            "status": "Статус",
            "kind": "Тип",
            "local": "Локально",
            "summary": "Кратко",
        }
        attachment_widths = {"label": 210, "status": 170, "kind": 80, "local": 140, "summary": 470}
        for column in attachment_columns:
            self.attachments_table.heading(column, text=attachment_headings[column])
            self.attachments_table.column(column, width=attachment_widths[column], anchor="w")
        attachment_scrollbar = ttk.Scrollbar(attachment_table_frame, orient="vertical", command=self.attachments_table.yview)
        self.attachments_table.configure(yscrollcommand=attachment_scrollbar.set)
        self.attachments_table.pack(side="left", fill="x", expand=True)
        attachment_scrollbar.pack(side="right", fill="y")

        attachment_buttons = ttk.Frame(attachments_frame)
        attachment_buttons.pack(fill="x", pady=(4, 0))
        ttk.Button(attachment_buttons, text="Открыть файл", command=self.open_selected_attachment, style="Modern.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(attachment_buttons, text="Открыть ссылку", command=self.open_selected_attachment_link, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(attachment_buttons, text="Скопировать отчет", command=self.copy_selected_attachment_report, style="Modern.TButton").pack(side="left", padx=6)

    def _create_rejections_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=BOTH, expand=True)
        ttk.Label(frame, text="Отсев", style="Panel.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        ttk.Label(frame, text="Заказы, которые система уже проверила и осознанно пропустила.", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=BOTH, expand=True)
        columns = ("posted", "title", "reason")
        self.rejections_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        headings = {"posted": "Дата", "title": "Название заказа", "reason": "Причина"}
        widths = {"posted": 120, "title": 440, "reason": 500}
        for column in columns:
            self.rejections_table.heading(column, text=headings[column])
            self.rejections_table.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.rejections_table.yview)
        self.rejections_table.configure(yscrollcommand=scrollbar.set)
        self.rejections_table.pack(side="left", fill=BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Обновить", command=self.refresh_rejections, style="Modern.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Открыть заказ", command=self.open_selected_rejection, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(buttons, text="Вернуть в проверку", command=self.restore_selected_rejection, style="Accent.TButton").pack(side="left", padx=6)

    def _create_log_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Лог", style="Panel.TLabel", font=("Segoe UI Semibold", 14)).pack(anchor="w")
        ttk.Label(parent, text="Здесь видны сканирование, ошибки отправки и действия с лидами.", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))
        self.log = scrolledtext.ScrolledText(parent, wrap="word", height=20, bg="#0f172a", fg="#dbeafe", insertbackground="#dbeafe", relief="flat", padx=12, pady=12, font=("Consolas", 10))
        self.log.pack(fill=BOTH, expand=True)
        self._bind_copyable_text(self.log)

    def _bind_copyable_text(self, widget) -> None:
        for sequence in ("<Control-c>", "<Control-C>", "<Control-Insert>", "<<Copy>>"):
            widget.bind(sequence, lambda event: _copy_widget_selection_to_clipboard(event.widget, self.root))

    def start_kwork_browser(self) -> None:
        script = ROOT_DIR / "start-kwork-browser.cmd"
        self._run_once(build_script_command(script), os.environ.copy(), "Kwork Chrome")

    def scan_once(self) -> None:
        command, env = build_app_command("scan")
        self._run_once(command, env, "Сканирование")

    def process_approvals(self) -> None:
        command, env = build_app_command("approvals")
        self._run_once(command, env, "Проверка почты")

    def refresh_leads(self) -> None:
        try:
            storage = self._storage()
            leads = storage.list_leads()
        except Exception as exc:
            self.write_log(f"Не удалось загрузить лиды: {exc}\n")
            return
        self.lead_rows.clear()
        self.leads_table.delete(*self.leads_table.get_children())
        target_item = None
        selected_lead_id = self.current_lead_id
        for lead in leads[:80]:
            item_id = self.leads_table.insert(
                "",
                END,
                values=build_lead_row_values(lead),
                tags=_lead_row_tags(lead),
            )
            self.lead_rows[item_id] = lead.id
            if lead.id == selected_lead_id:
                target_item = item_id
        children = self.leads_table.get_children()
        if target_item is None and children:
            target_item = children[0]
        if target_item is not None:
            self.leads_table.selection_set(target_item)
            self.leads_table.focus(target_item)
            self.leads_table.see(target_item)
            self.on_lead_select()
        else:
            self._clear_lead_details()
        self.refresh_rejections()

    def refresh_rejections(self) -> None:
        table = getattr(self, "rejections_table", None)
        if table is None:
            return
        try:
            rejections = self._storage().list_post_rejections(limit=200)
        except Exception as exc:
            self.write_log(f"Не удалось загрузить отсев: {exc}\n")
            return
        self.rejection_rows.clear()
        table.delete(*table.get_children())
        for rejection in rejections:
            item_id = table.insert(
                "",
                END,
                values=(
                    _format_datetime(rejection.posted_at or rejection.rejected_at),
                    _post_title(rejection.post_text),
                    rejection.reason,
                ),
            )
            self.rejection_rows[item_id] = rejection

    def _selected_rejection(self) -> PostRejection | None:
        selected = self.rejections_table.selection()
        if not selected:
            messagebox.showwarning("Заказ не выбран", "Выбери заказ в таблице отсева.")
            return None
        return self.rejection_rows.get(selected[0])

    def open_selected_rejection(self) -> None:
        rejection = LeadFunnelGui._selected_rejection(self)
        if rejection is None:
            return
        self._run_lead_action(
            "Открытие отклоненного заказа",
            lambda: self._open_url_in_kwork_chrome(rejection.post_url),
        )

    def restore_selected_rejection(self) -> None:
        rejection = LeadFunnelGui._selected_rejection(self)
        if rejection is None:
            return
        self._storage().clear_post_rejection(rejection.post_id)
        self.status_var.set(f"Заказ возвращен в проверку: {_post_title(rejection.post_text)}")
        self.write_log(f"Заказ {rejection.post_id} возвращен в проверку.\n")
        self.refresh_rejections()

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
        self.lead_url_var.set(lead.contact or lead.post_url)
        draft_reply = self.pending_replies.get(lead.id, lead.draft_reply)
        attachments = self._attachments_for_lead(lead)
        reply_context = _reply_context_from_lead(
            lead,
            title=_lead_title(lead),
            days=_extract_days(lead) or 3,
            attachments=attachments,
        )
        reply_notice = reply_delivery_issue_summary(draft_reply, reply_context)
        status = lead_status_summary(
            lead,
            pending_reply=lead.id in self.pending_replies,
            reply_notice=reply_notice,
            action_error=getattr(self, "lead_action_errors", {}).get(lead.id, ""),
        )
        self.lead_status_var.set(status)
        LeadFunnelGui._sync_kwork_price_limit_button(self, lead.id)
        self.summary_text.delete("1.0", END)
        self.summary_text.insert("1.0", _lead_details_text(lead))
        self.reply_text.delete("1.0", END)
        self.reply_text.insert("1.0", draft_reply)
        self._load_lead_attachments(lead, attachments)

    def save_lead_edits(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        try:
            self._save_lead_payload(lead, self._lead_payload(lead))
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.write_log(f"Лид #{lead.id}: название, цена, срок и текст отклика сохранены.\n")
        self.refresh_leads()

    def apply_kwork_price_limit(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        price_limit = self.kwork_price_limits.get(lead.id)
        if price_limit is None:
            messagebox.showinfo("Лимит Kwork", "Kwork пока не сообщил допустимую цену для этого лида.")
            return
        self.lead_price_var.set(str(price_limit))
        self.lead_status_var.set(
            f"Лид #{lead.id}: цена заменена на максимум Kwork {price_limit:,} руб.".replace(",", " ")
            + "; проверь и нажми «Сохранить» или «OK и отправить отклик»."
        )
        self.write_log(f"Лид #{lead.id}: в поле цены подставлен максимум Kwork {price_limit} руб.\n")

    def open_selected_lead(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        self._run_lead_action("Открытие заказа", lambda: self._open_kwork_lead(lead), lead_id=lead.id)

    def regenerate_selected_reply(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        if self.reply_regeneration_in_flight:
            messagebox.showinfo("Пересборка отклика", "Пересборка отклика уже выполняется.")
            return
        try:
            title = self.lead_title_var.get().strip() or _lead_title(lead)
            if not title or _is_placeholder_lead_title(title):
                raise ValueError("Название заказа обязательно")
            days = _parse_optional_int(self.lead_days_var.get(), "Срок") or _extract_days(lead) or 3
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        attachments = self._attachments_for_lead(lead)
        context = _reply_context_from_lead(lead, title=title, days=days, attachments=attachments)
        seed_reply = self.reply_text.get("1.0", END).strip()
        config = load_config()
        self.reply_regeneration_in_flight = True
        self.regenerate_reply_button.config(state=DISABLED)
        self.status_var.set(f"Пересборка отклика #{lead.id}: выполняется")
        self.write_log(f"=== Пересборка отклика #{lead.id}: старт ===\n")
        threading.Thread(
            target=self._regenerate_reply_thread,
            args=(lead.id, context, seed_reply, config.deepseek_api_key, config.deepseek_model),
            daemon=True,
        ).start()

    def _regenerate_reply_thread(
        self,
        lead_id: int,
        context: ReplyDraftContext,
        seed_reply: str,
        api_key: str,
        model: str,
    ) -> None:
        try:
            reply = compose_customer_reply(context, seed_reply, api_key=api_key, model=model)
        except Exception as exc:
            self.write_log(f"=== Пересборка отклика #{lead_id}: ошибка: {exc} ===\n")
            self.root.after(0, lambda: self.status_var.set(f"Пересборка отклика #{lead_id}: ошибка"))
        else:
            self.write_log(f"=== Пересборка отклика #{lead_id}: черновик готов ===\n")
            self.root.after(0, lambda: self._apply_regenerated_reply(lead_id, reply))
        finally:
            self.root.after(0, self._finish_reply_regeneration)

    def _apply_regenerated_reply(self, lead_id: int, reply: str) -> None:
        clean_reply = reply.strip()
        if not clean_reply:
            self.write_log(f"=== Пересборка отклика #{lead_id}: пустой результат ===\n")
            return
        self.pending_replies[lead_id] = clean_reply
        if self.current_lead_id == lead_id:
            self.reply_text.delete("1.0", END)
            self.reply_text.insert("1.0", clean_reply)
            self.lead_status_var.set(f"Лид #{lead_id}: новый черновик готов, не сохранен.")

    def _finish_reply_regeneration(self) -> None:
        self.reply_regeneration_in_flight = False
        self.regenerate_reply_button.config(state=NORMAL)

    def open_selected_lead_from_url(self, _event=None) -> str:
        self.open_selected_lead()
        return "break"

    def copy_selected_lead_url(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        url = lead.contact or lead.post_url
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.lead_status_var.set(f"Ссылка скопирована: {url}")

    def open_selected_attachment(self) -> None:
        attachment = self._selected_attachment()
        if attachment is None:
            return
        if attachment.local_path and Path(attachment.local_path).exists():
            self._open_local_path(Path(attachment.local_path))
            self.lead_status_var.set(f"Открыт файл: {attachment.local_path}")
            return
        if attachment.url:
            self._open_url_in_kwork_chrome(attachment.url)
            self.lead_status_var.set(f"Открыта ссылка вложения: {attachment.url}")
            return
        messagebox.showwarning("Вложение", "У вложения нет локального файла или ссылки.")

    def open_selected_attachment_link(self) -> None:
        attachment = self._selected_attachment()
        if attachment is None:
            return
        if not attachment.url:
            messagebox.showwarning("Вложение", "У вложения нет ссылки.")
            return
        self._open_url_in_kwork_chrome(attachment.url)
        self.lead_status_var.set(f"Открыта ссылка вложения: {attachment.url}")

    def copy_selected_attachment_report(self) -> None:
        attachment = self._selected_attachment()
        if attachment is None:
            return
        report = _attachment_report_text(attachment)
        self.root.clipboard_clear()
        self.root.clipboard_append(report)
        self.lead_status_var.set(f"Отчет по вложению скопирован: {attachment.label}")

    def prepare_selected_lead(self) -> None:
        lead = self._selected_lead()
        if lead is None:
            return
        try:
            payload = self._lead_payload(lead)
            self._save_lead_payload(lead, payload)
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
        block_reason = lead_send_block_reason(lead, self.in_flight_lead_ids)
        if block_reason:
            messagebox.showinfo("Отправка отклика", block_reason)
            return
        try:
            payload = self._lead_payload(lead)
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        attachments = self._attachments_for_lead(lead)
        context = _reply_context_from_lead(
            lead,
            title=payload["title"],
            days=payload["days"] or _extract_days(lead) or 3,
            attachments=attachments,
        )
        quality_block_reason = direct_send_reply_block_reason(payload["reply"], context)
        if quality_block_reason:
            messagebox.showwarning("Отклик требует правки", quality_block_reason)
            self.lead_status_var.set(f"Лид #{lead.id}: отклик требует правки перед отправкой.")
            return
        self._save_lead_payload(lead, payload)
        if not messagebox.askyesno("OK и отправить отклик", direct_send_confirmation(lead, payload)):
            return
        self.in_flight_lead_ids.add(lead.id)
        self.send_lead_button.config(state=DISABLED)
        self._run_lead_action(
            f"Отправка лида #{lead.id}",
            lambda: self._send_lead_now(lead, payload),
            lead_id=lead.id,
            on_finished=lambda: self._release_lead_send(lead.id),
            mark_failed=True,
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

    def _release_lead_send(self, lead_id: int) -> None:
        self.in_flight_lead_ids.discard(lead_id)
        self.send_lead_button.config(state=NORMAL)

    def _run_lead_action(
        self,
        label: str,
        action,
        lead_id: int | None = None,
        on_finished=None,
        mark_failed: bool = False,
    ) -> None:
        if lead_id is not None:
            self.lead_action_errors.pop(lead_id, None)
            self.kwork_price_limits.pop(lead_id, None)
            LeadFunnelGui._sync_kwork_price_limit_button(self, lead_id)
        self.status_var.set(f"{label}: выполняется")
        self.write_log(f"=== {label}: старт ===\n")
        threading.Thread(
            target=self._run_lead_action_thread,
            args=(label, action, lead_id, on_finished, mark_failed),
            daemon=True,
        ).start()

    def _run_lead_action_thread(
        self,
        label: str,
        action,
        lead_id: int | None,
        on_finished=None,
        mark_failed: bool = False,
    ) -> None:
        try:
            result = action()
        except Exception as exc:
            if mark_failed and lead_id is not None:
                try:
                    self._storage().mark_failed(lead_id, str(exc))
                except Exception:
                    pass
            self.write_log(f"=== {label}: ошибка: {exc} ===\n")
            self.root.after(0, lambda: self.status_var.set(f"{label}: ошибка"))
            if lead_id is not None:
                self.root.after(0, lambda: LeadFunnelGui._show_lead_action_error(self, lead_id, str(exc)))
        else:
            self.write_log(f"=== {label}: готово ({result}) ===\n")
            self.root.after(0, lambda: self.status_var.set(f"{label}: готово"))
        finally:
            if on_finished is not None:
                self.root.after(0, on_finished)
            self.root.after(0, self.refresh_leads)

    def _show_lead_action_error(self, lead_id: int, error: str) -> None:
        action_errors = getattr(self, "lead_action_errors", None)
        if action_errors is not None:
            action_errors[lead_id] = error
        price_limit = _kwork_price_limit(error)
        if price_limit is not None:
            price_limits = getattr(self, "kwork_price_limits", None)
            if price_limits is not None:
                price_limits[lead_id] = price_limit
        if getattr(self, "current_lead_id", None) != lead_id:
            return
        LeadFunnelGui._sync_kwork_price_limit_button(self, lead_id)
        lead_status = getattr(self, "lead_status_var", None)
        if lead_status is not None:
            lead_status.set(f"Лид #{lead_id}: ошибка: {error}")

    def _sync_kwork_price_limit_button(self, lead_id: int | None) -> None:
        button = getattr(self, "apply_kwork_price_button", None)
        if button is None:
            return
        price_limits = getattr(self, "kwork_price_limits", {})
        state = NORMAL if lead_id is not None and lead_id in price_limits else DISABLED
        button.config(state=state)

    def _lead_payload(self, lead: Lead) -> dict:
        raw_reply = self.reply_text.get("1.0", END).strip()
        if not raw_reply:
            raise ValueError("Текст отклика пустой")
        title = self.lead_title_var.get().strip() or _lead_title(lead)
        if not title or _is_placeholder_lead_title(title):
            raise ValueError("Название заказа обязательно")
        days = _parse_optional_int(self.lead_days_var.get(), "Срок")
        reply = sanitize_customer_reply(
            raw_reply,
            summary=title,
            estimated_days=days or _extract_days(lead) or 3,
        )
        return {
            "reply": reply,
            "title": title,
            "price": _parse_optional_int(self.lead_price_var.get(), "Цена"),
            "days": days,
        }

    def _save_lead_payload(self, lead: Lead, payload: dict) -> None:
        self._storage().update_lead_proposal(
            lead.id,
            draft_reply=payload["reply"],
            title=payload["title"],
            price_rub=payload["price"],
            days=payload["days"],
        )
        self.pending_replies.pop(lead.id, None)

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
            max_responses=config.kwork_max_responses,
            cookie=config.kwork_cookie,
        )

    def _open_kwork_lead(self, lead: Lead) -> str:
        self._open_url_in_kwork_chrome(lead.contact)
        return f"opened lead {lead.id}"

    def _open_url_in_kwork_chrome(self, url: str) -> str:
        from app import kwork_source

        config = load_config()
        kwork_source._ensure_chrome_cdp(config.kwork_cdp_url, url, config.kwork_browser_profile_dir)
        version = kwork_source._cdp_json(config.kwork_cdp_url, "/json/version", timeout=5)
        if not version:
            raise RuntimeError("Chrome DevTools недоступен")
        import websocket

        ws = websocket.create_connection(version["webSocketDebuggerUrl"], timeout=10)
        try:
            kwork_source._send_cdp(ws, "Target.createTarget", {"url": url})
        finally:
            ws.close()
        return f"opened {url}"

    def _open_local_path(self, path: Path) -> None:
        if os.name == "nt":
            os.startfile(str(path))
            return
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
        self.status_var.set("Мониторинг запущен")
        self.start_watch_button.config(state=DISABLED)
        self.stop_watch_button.config(state=NORMAL)
        self.write_log("=== Мониторинг запущен ===\n")
        self._schedule_watch_refresh()
        threading.Thread(target=self._stream_process, args=(self.watch_process, "Мониторинг"), daemon=True).start()

    def stop_watch(self) -> None:
        if not self.watch_process or self.watch_process.poll() is not None:
            self.status_var.set("Мониторинг не запущен")
            self.start_watch_button.config(state=NORMAL)
            self.stop_watch_button.config(state=DISABLED)
            self._cancel_watch_refresh()
            return
        self._cancel_watch_refresh()
        self.watch_process.terminate()
        try:
            self.watch_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.watch_process.kill()
        self.status_var.set("Мониторинг остановлен")
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
            f"возраст <= {values.get('KWORK_MAX_AGE_HOURS', '24')} ч., "
            f"AI score >= {values.get('LEAD_MIN_SCORE', '60')}, "
            f"срок <= {values.get('LEAD_MAX_DAYS', '7')} дн., "
            f"решения: {values.get('LEAD_ACCEPT_DECISIONS', 'accept, maybe')}, "
            f"стоп-слова: {values.get('LEAD_BLOCKED_KEYWORDS', 'битрикс, bitrix')}.\n"
        )

    def close(self) -> None:
        self._cancel_watch_refresh()
        self.stop_watch()
        self.root.destroy()

    def _run_once(self, command: list[str], env: dict[str, str], label: str) -> None:
        if not LeadFunnelGui._begin_once_action(self, label):
            return
        self.status_var.set(f"{label}: выполняется")
        self.write_log(f"=== {label}: старт ===\n")
        threading.Thread(target=self._run_once_thread, args=(command, env, label), daemon=True).start()

    def _run_once_thread(self, command: list[str], env: dict[str, str], label: str) -> None:
        try:
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
        except Exception as exc:
            self.root.after(0, lambda: self.status_var.set(f"{label}: ошибка"))
            self.write_log(f"=== {label}: не удалось запустить: {exc} ===\n")
        else:
            return_code = process.returncode
            if return_code == 0:
                self.root.after(0, lambda: self.status_var.set(f"{label}: завершено"))
            else:
                self.root.after(0, lambda: self.status_var.set(f"{label}: ошибка (код {return_code})"))
            self.write_log(f"=== {label}: завершено с кодом {return_code} ===\n")
            if _should_refresh_after_process(label):
                self.root.after(0, self.refresh_leads)
        finally:
            self.root.after(0, lambda: LeadFunnelGui._finish_once_action(self, label))

    def _begin_once_action(self, label: str) -> bool:
        running_actions = getattr(self, "running_once_actions", set())
        if label in running_actions:
            self.write_log(f"{label} уже выполняется.\n")
            return False
        running_actions.add(label)
        button = getattr(self, "once_action_buttons", {}).get(label)
        if button is not None:
            button.config(state=DISABLED)
        return True

    def _finish_once_action(self, label: str) -> None:
        getattr(self, "running_once_actions", set()).discard(label)
        button = getattr(self, "once_action_buttons", {}).get(label)
        if button is not None:
            button.config(state=NORMAL)

    def _stream_process(self, process: subprocess.Popen[str], label: str) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            self.write_log(line)
        process.wait()
        if process is self.watch_process:
            self.root.after(0, self._cancel_watch_refresh)
            self.root.after(0, self.refresh_leads)
            self.root.after(0, lambda: self.start_watch_button.config(state=NORMAL))
            self.root.after(0, lambda: self.stop_watch_button.config(state=DISABLED))
            self.root.after(0, lambda: self.status_var.set(f"{label}: остановлен"))

    def write_log(self, text: str) -> None:
        self.root.after(0, lambda: self._append_log(text))

    def _append_log(self, text: str) -> None:
        self.log.insert(END, text)
        self.log.see(END)

    def _schedule_watch_refresh(self) -> None:
        self._cancel_watch_refresh()
        self._refresh_leads_while_watching()

    def _refresh_leads_while_watching(self) -> None:
        if not self.watch_process or self.watch_process.poll() is not None:
            self.watch_refresh_after_id = None
            return
        self.refresh_leads()
        self.watch_refresh_after_id = self.root.after(WATCH_REFRESH_MS, self._refresh_leads_while_watching)

    def _cancel_watch_refresh(self) -> None:
        if not self.watch_refresh_after_id:
            return
        try:
            self.root.after_cancel(self.watch_refresh_after_id)
        except TclError:
            pass
        self.watch_refresh_after_id = None

    def _load_lead_attachments(
        self,
        lead: Lead,
        attachments: list[LeadAttachment] | None = None,
    ) -> None:
        self.attachment_rows.clear()
        self.attachments_table.delete(*self.attachments_table.get_children())
        if attachments is None:
            attachments = self._attachments_for_lead(lead)
        for attachment in attachments:
            item_id = self.attachments_table.insert("", END, values=_attachment_row_values(attachment))
            self.attachment_rows[item_id] = attachment

    def _attachments_for_lead(self, lead: Lead) -> list[LeadAttachment]:
        try:
            attachments = self._storage().list_lead_attachments(lead.id)
        except Exception as exc:
            self.write_log(f"Не удалось загрузить вложения лида #{lead.id}: {exc}\n")
            attachments = []
        if not attachments:
            attachments = _fallback_attachments_from_summary(lead)
        return attachments

    def _selected_attachment(self) -> LeadAttachment | None:
        selected = self.attachments_table.selection()
        if not selected:
            messagebox.showwarning("Вложение не выбрано", "Выбери вложение в таблице.")
            return None
        return self.attachment_rows.get(selected[0])

    def _clear_lead_details(self) -> None:
        self.current_lead_id = None
        self.lead_title_var.set("")
        self.lead_price_var.set("")
        self.lead_days_var.set("")
        self.lead_url_var.set("")
        self.lead_status_var.set("Лид не выбран")
        self.summary_text.delete("1.0", END)
        self.reply_text.delete("1.0", END)
        self.attachment_rows.clear()
        self.attachments_table.delete(*self.attachments_table.get_children())


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


def _copy_widget_selection_to_clipboard(widget, clipboard_owner) -> str | None:
    try:
        selected_text = widget.get("sel.first", "sel.last")
    except (TclError, AttributeError):
        return None
    if not selected_text:
        return None
    clipboard_owner.clipboard_clear()
    clipboard_owner.clipboard_append(selected_text)
    return "break"


def _attachment_row_values(attachment: LeadAttachment) -> tuple[str, str, str, str, str]:
    return (
        attachment.label,
        attachment.status,
        attachment.kind,
        _attachment_local_state(attachment),
        attachment.summary,
    )


def _fallback_attachments_from_summary(lead: Lead) -> list[LeadAttachment]:
    marker = "ФАЙЛЫ/ТЗ:"
    if marker not in lead.summary:
        return []

    section = lead.summary.split(marker, 1)[1]
    blocks = [block.strip() for block in re.split(r"\n\s*(?=-\s+)", section.strip()) if block.strip()]
    attachments: list[LeadAttachment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("- "):
            continue
        label = lines[0].removeprefix("- ").strip()
        url = _read_attachment_field(block, "Ссылка")
        status = _read_attachment_field(block, "Статус")
        summary = _read_attachment_field(block, "Кратко")
        if not label and not url:
            continue
        kind = _attachment_kind_from_values(label, url, status)
        attachments.append(
            LeadAttachment(
                id=0,
                lead_id=lead.id,
                label=label or "attachment",
                url=url,
                local_path="",
                status=status or "нет отчета",
                summary=summary,
                kind=kind,
                opened_archive="архив открыт" in status.lower(),
                ocr_scanned="ocr" in status.lower(),
            )
        )
    return attachments


def _attachment_report_text(attachment: LeadAttachment) -> str:
    return "\n".join(
        [
            f"Файл: {attachment.label}",
            f"Ссылка: {attachment.url or '-'}",
            f"Локально: {attachment.local_path or '-'}",
            f"Статус: {attachment.status or '-'}",
            f"Тип: {attachment.kind or 'file'}",
            f"Архив открыт: {'да' if attachment.opened_archive else 'нет'}",
            f"OCR/фото прочитано: {'да' if attachment.ocr_scanned else 'нет'}",
            "Кратко:",
            attachment.summary or "-",
        ]
    )


def _attachment_local_state(attachment: LeadAttachment) -> str:
    if not attachment.local_path:
        return "нет локального файла"
    path = Path(attachment.local_path)
    return path.name if path.exists() else "файл не найден"


def _read_attachment_field(block: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}:\s*(.*)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _attachment_kind_from_values(label: str, url: str, status: str) -> str:
    haystack = f"{label} {url} {status}".lower()
    if any(ext in haystack for ext in (".zip", ".rar", ".7z")) or "архив" in haystack:
        return "archive"
    if ".pdf" in haystack:
        return "pdf"
    if any(ext in haystack for ext in (".doc", ".docx", ".rtf", ".odt")):
        return "document"
    if any(ext in haystack for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")) or "ocr" in haystack:
        return "image"
    if any(ext in haystack for ext in (".txt", ".md", ".csv", ".html", ".htm")):
        return "text"
    return "file"


def _extract_price(lead: Lead) -> int | None:
    if lead.proposal_price_rub is not None:
        return lead.proposal_price_rub
    terms = _extract_reply_terms(lead.draft_reply)
    if terms.price_rub is not None:
        return terms.price_rub
    import re

    match = re.search(r"Цена:\s*(\d[\d\s]*)\s*руб", lead.summary, re.IGNORECASE)
    return int(match.group(1).replace(" ", "")) if match else None


def _extract_days(lead: Lead) -> int | None:
    if lead.proposal_days is not None:
        return lead.proposal_days
    terms = _extract_reply_terms(lead.draft_reply)
    if terms.days is not None:
        return terms.days
    import re

    match = re.search(r"Срок:\s*(\d{1,2})\s*дн", lead.summary, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _lead_title(lead: Lead) -> str:
    if lead.proposal_title:
        return lead.proposal_title
    for line in lead.post_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("\U0001f4cc"):
            return clean.lstrip("\U0001f4cc").strip()[:70]
        if _looks_like_kwork_meta_line(clean):
            continue
        return clean[:70]
    for line in lead.summary.splitlines():
        clean = line.strip()
        if clean.startswith("Задача:"):
            return clean.removeprefix("Задача:").strip()[:70]
    first_line = next((line.strip() for line in lead.summary.splitlines() if line.strip()), "")
    return (first_line or f"Kwork lead {lead.id}")[:70]


def _post_title(post_text: str) -> str:
    for line in post_text.splitlines():
        clean = line.strip().lstrip("📌").strip()
        if clean and not _looks_like_kwork_meta_line(clean):
            return clean[:180]
    return "Заказ без названия"


def _is_placeholder_lead_title(value: str) -> bool:
    return bool(re.fullmatch(r"Kwork lead \d+", value.strip(), re.IGNORECASE))


def _lead_task_summary(lead: Lead) -> str:
    for line in lead.summary.splitlines():
        clean = line.strip()
        if clean.startswith("Задача:"):
            return clean.removeprefix("Задача:").strip() or _lead_title(lead)
    return _lead_title(lead) or "вашу задачу"


def _reply_context_from_lead(
    lead: Lead,
    title: str,
    days: int,
    attachments: list[LeadAttachment],
) -> ReplyDraftContext:
    attachment_context = "\n".join(
        f"{attachment.label}: {(attachment.summary or attachment.status).strip()}"
        for attachment in attachments
        if attachment.label.strip() and (attachment.summary or attachment.status).strip()
    )
    task_summary = title.strip() or _lead_title(lead) or "вашу задачу"
    return ReplyDraftContext(
        title=title,
        task_summary=task_summary,
        source_text=lead.post_text.strip(),
        attachment_context=attachment_context,
        estimated_days=max(1, days),
    )


def build_lead_row_values(lead: Lead) -> tuple:
    return (
        lead.id,
        _format_datetime(lead.posted_at or lead.created_at),
        _extract_offer_count(lead) or "",
        _reply_state(lead),
        lead.status,
        lead.score,
        _extract_price(lead) or "",
        _extract_days(lead) or "",
        _lead_title(lead),
    )


def _lead_details_text(lead: Lead) -> str:
    offer_count = _extract_offer_count(lead)
    remaining = _extract_remaining_time(lead)
    lines = [
        f"Название: {_lead_title(lead)}",
        f"Ссылка: {lead.contact or lead.post_url}",
        f"Дата: {_format_datetime(lead.posted_at or lead.created_at)}",
        f"Предложений: {offer_count if offer_count is not None else 'не найдено'}",
        f"Осталось: {remaining or 'не найдено'}",
        f"Наш отклик: {_reply_state(lead)}",
        f"Статус: {lead.status}; score: {lead.score}",
    ]
    if lead.channel or lead.message_id:
        lines.append(f"Источник: {lead.channel or 'unknown'} / {lead.message_id or '-'}")
    if lead.last_error:
        lines.append(f"Ошибка: {lead.last_error}")
    lines.extend(
        [
            "",
            "--- КАРТОЧКА KWORK ---",
            lead.post_text.strip() or "Карточка заказа не сохранена.",
            "",
            "--- AI-ОЦЕНКА ---",
            lead.summary.strip() or "AI-оценка пустая.",
        ]
    )
    return "\n".join(lines)


def _extract_offer_count(lead: Lead) -> int | None:
    for text in (lead.post_text, lead.summary):
        match = re.search(r"Предложений:\s*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _extract_remaining_time(lead: Lead) -> str:
    for text in (lead.post_text, lead.summary):
        match = re.search(r"Осталось:\s*(.*?)(?:\s+Предложений:|\n|$)", text, re.IGNORECASE)
        if match:
            return _clean_meta_value(match.group(1))
    return ""


def _reply_state(lead: Lead) -> str:
    if lead.sent_at:
        return f"отправлен {_format_datetime(lead.sent_at)}"
    if lead.status == "sent":
        return "отправлен"
    return "нет"


def lead_status_summary(
    lead: Lead,
    *,
    pending_reply: bool,
    reply_notice: str = "",
    action_error: str = "",
) -> str:
    """Build the concise state shown above the selected lead's editable fields."""
    status = (
        f"Лид #{lead.id}: {lead.status}; score {lead.score}; "
        f"предложений: {_extract_offer_count(lead) or 'не видно'}; наш отклик: {_reply_state(lead)}"
    )
    if reply_notice:
        status += f"; {reply_notice}"
    if pending_reply:
        status += "; новый черновик не сохранен"

    errors = [error.strip() for error in (lead.last_error, action_error) if error.strip()]
    for error in dict.fromkeys(errors):
        status += f"; ошибка: {error}"
    return status


def lead_send_block_reason(lead: Lead, in_flight_lead_ids: set[int]) -> str:
    if lead.status == "sent" or lead.sent_at:
        return "Отклик по этому лиду уже отправлен."
    if lead.id in in_flight_lead_ids:
        return "Отправка этого лида уже выполняется."
    return ""


def direct_send_confirmation(lead: Lead, payload: dict) -> str:
    title = str(payload.get("title") or _lead_title(lead) or f"лид #{lead.id}").strip()
    price = payload.get("price")
    days = payload.get("days")
    price_text = f"{int(price):,}".replace(",", " ") + " руб." if isinstance(price, int) else "не указана"
    days_text = f"{days} дн." if isinstance(days, int) else "не указан"
    return (
        f"Отправить отклик по заказу:\n{title}\n\n"
        f"Цена: {price_text}\n"
        f"Срок: {days_text}\n\n"
        "Сообщение и параметры будут отправлены на Kwork сейчас."
    )


def direct_send_reply_block_reason(reply: str, context: ReplyDraftContext) -> str:
    """Explain why a draft cannot be submitted until it is made fact-safe."""
    labels = reply_delivery_issue_labels(reply, context)
    if not labels:
        return ""
    return (
        "Отклик не отправлен: в тексте есть не подтвержденные фактами заказа формулировки: "
        + "; ".join(labels)
        + ".\n\nПересобери отклик или исправь текст и повтори отправку."
    )


def _lead_row_tags(lead: Lead) -> tuple[str, ...]:
    tags = [lead.status]
    if lead.score < 70 and lead.status != "sent":
        tags.append("low_score")
    return tuple(tags)


def _format_datetime(value: str) -> str:
    clean = value.strip()
    if not clean:
        return "-"
    normalized = clean.replace("Z", "+00:00")
    for parser in (
        lambda item: datetime.fromisoformat(item),
        lambda item: datetime.strptime(item, "%Y-%m-%d %H:%M:%S"),
        lambda item: datetime.strptime(item, "%Y-%m-%d %H:%M"),
    ):
        try:
            parsed = parser(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=MOSCOW_TZ)
            return parsed.astimezone(MOSCOW_TZ).strftime("%d.%m %H:%M МСК")
        except ValueError:
            continue
    return clean.replace("T", " ")[:16]


def _should_refresh_after_process(label: str) -> bool:
    return label in REFRESH_AFTER_LABELS


def _looks_like_kwork_meta_line(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("осталось:", "предложений:", "отклик:", "kwork title:", "kwork description:"))


def _clean_meta_value(value: str) -> str:
    return " ".join(value.split()).strip(" ;")


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


def _kwork_price_limit(error: str) -> int | None:
    """Extract Kwork's allowed maximum from the inline validation error."""
    match = re.search(r"стоимость\s+может\s+быть\s+не\s+более\s+(\d[\d\s]*)\s*руб", error, re.IGNORECASE)
    if not match:
        return None
    value = re.sub(r"\D", "", match.group(1))
    return int(value) if value else None


if __name__ == "__main__":
    raise SystemExit(main())
