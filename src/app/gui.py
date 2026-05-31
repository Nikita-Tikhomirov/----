from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, Button, Label, Tk, scrolledtext


ROOT_DIR = Path(__file__).resolve().parents[2]


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
        self.root.geometry("900x560")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.watch_process: subprocess.Popen[str] | None = None

        self.status = Label(root, text="Готово", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(10, 4))

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


if __name__ == "__main__":
    raise SystemExit(main())
