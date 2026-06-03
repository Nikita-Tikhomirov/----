from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, Button, Entry, Label, LabelFrame, StringVar, Tk, messagebox, scrolledtext


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

        self.status = Label(root, text="Готово", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(10, 4))

        self._create_settings_panel()

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

        self.log = scrolledtext.ScrolledText(root, wrap="word", height=24)
        self.log.pack(fill=BOTH, expand=True, padx=10, pady=(8, 10))
        self.write_log("Открой Kwork Chrome, войди в Kwork один раз, затем запускай сканирование или мониторинг.\n")
        self.write_log(self._filter_summary())

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

    def start_kwork_browser(self) -> None:
        script = ROOT_DIR / "start-kwork-browser.cmd"
        self._run_once(build_script_command(script), os.environ.copy(), "Kwork Chrome")

    def scan_once(self) -> None:
        command, env = build_app_command("scan")
        self._run_once(command, env, "Сканирование")

    def process_approvals(self) -> None:
        command, env = build_app_command("approvals")
        self._run_once(command, env, "Проверка OK")

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


if __name__ == "__main__":
    raise SystemExit(main())
