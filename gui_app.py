"""Work Timer — оконная версия.

Весь отсчёт идёт через ``root.after``: один поток, никаких sleep внутри
обработчиков. Прежняя версия крутила ``while ... time.sleep(1)`` прямо в
главном потоке, и окно намертво замирало после первого же перерыва.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from src import notify, storage
from src.timer import Event, Phase, WorkTimer

TICK_MS = 200

COLORS = {
    "bg": "#f4f6f8",
    "header": "#2c3e50",
    "text": "#2c3e50",
    "muted": "#7f8c8d",
    "work": "#27ae60",
    "break": "#e67e22",
    "paused": "#f39c12",
    "stopped": "#95a5a6",
    "danger": "#e74c3c",
    "accent": "#3498db",
}


class WorkTimerApp:
    """Главное окно."""

    def __init__(self) -> None:
        self.settings = storage.load_settings()
        self.timer = WorkTimer(
            work_minutes=float(self.settings["work_minutes"]),
            blink_minutes=float(self.settings["blink_minutes"]),
            break_minutes=float(self.settings["break_minutes"]),
        )
        self.started_at: datetime | None = None

        self.root = tk.Tk()
        self.root.title("Work Timer — забота о здоровье")
        self.root.geometry("560x730")
        self.root.minsize(520, 640)
        self.root.configure(bg=COLORS["bg"])

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._tick()

    # ================================================================
    # Интерфейс
    # ================================================================

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=COLORS["header"], height=86)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="🧘  WORK TIMER", font=("Segoe UI", 22, "bold"),
            bg=COLORS["header"], fg="white",
        ).pack(pady=(16, 0))
        tk.Label(
            header, text="перерывы, разминка и напоминания моргать",
            font=("Segoe UI", 9), bg=COLORS["header"], fg="#bdc3c7",
        ).pack()

        body = tk.Frame(self.root, bg=COLORS["bg"], padx=22, pady=16)
        body.pack(fill="both", expand=True)

        self.status_label = tk.Label(
            body, text="⏹ Остановлен", font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg"], fg=COLORS["stopped"],
        )
        self.status_label.pack()

        self.countdown_label = tk.Label(
            body, text="--:--", font=("Segoe UI", 46, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"],
        )
        self.countdown_label.pack(pady=(2, 0))

        self.progress = ttk.Progressbar(body, mode="determinate", maximum=1000)
        self.progress.pack(fill="x", pady=(6, 10))

        # Сообщение вместо модального окна: раньше messagebox замораживал
        # отсчёт до тех пор, пока пользователь не нажмёт «ОК».
        self.banner = tk.Label(
            body, text="Нажмите «Старт», и таймер начнёт следить за временем",
            font=("Segoe UI", 11), bg="#dff0d8", fg="#2c3e50",
            wraplength=470, justify="center", padx=10, pady=10,
        )
        self.banner.pack(fill="x")

        self._build_buttons(body)
        self._build_stats(body)
        self._build_settings(body)

    def _build_buttons(self, parent: tk.Widget) -> None:
        row = tk.Frame(parent, bg=COLORS["bg"])
        row.pack(pady=14)

        self.start_button = self._button(row, "▶ Старт", COLORS["work"], self.start)
        self.start_button.grid(row=0, column=0, padx=4)
        self.pause_button = self._button(row, "⏸ Пауза", COLORS["paused"], self.toggle_pause)
        self.pause_button.grid(row=0, column=1, padx=4)
        self.stop_button = self._button(row, "⏹ Стоп", COLORS["danger"], self.stop)
        self.stop_button.grid(row=0, column=2, padx=4)
        self.skip_button = self._button(row, "⏭ Пропустить", COLORS["accent"], self.skip_break)
        self.skip_button.grid(row=0, column=3, padx=4)

        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.skip_button.config(state="disabled")

    def _button(self, parent: tk.Widget, text: str, colour: str, command) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command, font=("Segoe UI", 11),
            bg=colour, fg="white", activebackground=colour, activeforeground="white",
            bd=0, relief="flat", padx=14, pady=8, cursor="hand2",
            disabledforeground="#ecf0f1",
        )

    def _build_stats(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(
            parent, text=" 📊 За этот сеанс ", font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"], padx=14, pady=10, bd=1, relief="solid",
        )
        frame.pack(fill="x")
        self.stats_label = tk.Label(
            frame, text="", font=("Consolas", 10), bg=COLORS["bg"],
            fg=COLORS["text"], justify="left", anchor="w",
        )
        self.stats_label.pack(fill="x")

        self.history_label = tk.Label(
            frame, text="", font=("Consolas", 9), bg=COLORS["bg"],
            fg=COLORS["muted"], justify="left", anchor="w",
        )
        self.history_label.pack(fill="x", pady=(8, 0))
        self._refresh_history()

    def _build_settings(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(
            parent, text=" ⚙️ Настройки ", font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"], padx=14, pady=10, bd=1, relief="solid",
        )
        frame.pack(fill="x", pady=(12, 0))

        self.vars = {}
        rows = (
            ("work_minutes", "Перерыв каждые"),
            ("blink_minutes", "Моргать каждые"),
            ("break_minutes", "Длительность перерыва"),
        )
        for index, (key, caption) in enumerate(rows):
            tk.Label(frame, text=caption, bg=COLORS["bg"], fg=COLORS["text"],
                     font=("Segoe UI", 10)).grid(row=index, column=0, sticky="w", pady=3)
            variable = tk.StringVar(value=f"{float(self.settings[key]):g}")
            self.vars[key] = variable
            tk.Spinbox(
                frame, textvariable=variable, from_=0.1, to=240, increment=1,
                width=7, font=("Segoe UI", 10), justify="center",
            ).grid(row=index, column=1, padx=8)
            tk.Label(frame, text="минут", bg=COLORS["bg"], fg=COLORS["muted"],
                     font=("Segoe UI", 9)).grid(row=index, column=2, sticky="w")

        self.sound_var = tk.BooleanVar(value=bool(self.settings["sound"]))
        tk.Checkbutton(
            frame, text="Звук напоминаний", variable=self.sound_var,
            bg=COLORS["bg"], fg=COLORS["text"], activebackground=COLORS["bg"],
            font=("Segoe UI", 10), selectcolor="white",
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

        self.long_blink_var = tk.BooleanVar(value=bool(self.settings["long_blink_sound"]))
        tk.Checkbutton(
            frame, text="Длинный звук для моргания (36 с)", variable=self.long_blink_var,
            bg=COLORS["bg"], fg=COLORS["muted"], activebackground=COLORS["bg"],
            font=("Segoe UI", 9), selectcolor="white",
        ).grid(row=4, column=0, sticky="w")

        tk.Button(
            frame, text="Сохранить", command=self.save_settings, font=("Segoe UI", 10),
            bg=COLORS["accent"], fg="white", bd=0, relief="flat", padx=16, pady=5,
            cursor="hand2",
        ).grid(row=3, column=1, rowspan=2, padx=8)

        tk.Label(
            frame, text="Дробные значения допустимы: 0.5 — это тридцать секунд",
            bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 8),
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))

    # ================================================================
    # Действия
    # ================================================================

    def start(self) -> None:
        self.timer.start()
        self.started_at = datetime.now()
        self.show_banner("Поехали. Отдыхать через "
                         f"{self.timer.work_minutes:g} мин.", "#dff0d8")
        self._refresh_buttons()

    def toggle_pause(self) -> None:
        self.timer.toggle_pause()
        self._refresh_buttons()

    def stop(self) -> None:
        if self.timer.running and self.started_at is not None:
            storage.append_session(
                self.timer.stats.as_dict(), self.started_at, datetime.now()
            )
            self._refresh_history()
        self.timer.stop()
        self.started_at = None
        self.show_banner("Сеанс записан в историю.", "#eaeded")
        self._refresh_buttons()

    def skip_break(self) -> None:
        self.timer.skip_break()
        self._refresh_buttons()

    def save_settings(self) -> None:
        try:
            values = {key: float(var.get().replace(",", ".")) for key, var in self.vars.items()}
        except ValueError:
            messagebox.showerror("Ошибка", "Интервалы задаются числом, например 30 или 0.5")
            return
        if any(value <= 0 for value in values.values()):
            messagebox.showerror("Ошибка", "Интервалы должны быть больше нуля")
            return

        self.settings.update(values)
        self.settings["sound"] = self.sound_var.get()
        self.settings["long_blink_sound"] = self.long_blink_var.get()
        storage.save_settings(self.settings)

        self.timer.work_minutes = values["work_minutes"]
        self.timer.blink_minutes = values["blink_minutes"]
        self.timer.break_minutes = values["break_minutes"]
        self.show_banner("Настройки сохранены и уже действуют.", "#d9edf7")

    # ================================================================
    # Ход времени
    # ================================================================

    def _tick(self) -> None:
        for event in self.timer.tick():
            self._handle_event(event)
        self._refresh_display()
        self.root.after(TICK_MS, self._tick)

    def _handle_event(self, event: Event) -> None:
        key = event.value
        title, text = notify.message(key)
        colour = {"blink": "#fcf8e3", "break_start": "#f9e0c9", "break_end": "#dff0d8"}
        self.show_banner(f"{title} — {text}", colour.get(key, "#eaeded"))
        if self.sound_var.get():
            notify.play(key, use_long_blink=self.long_blink_var.get())
        # Окно всплывает поверх других, но не перехватывает ввод.
        if key in ("break_start", "break_end"):
            self.root.attributes("-topmost", True)
            self.root.after(2500, lambda: self.root.attributes("-topmost", False))

    def _refresh_display(self) -> None:
        timer = self.timer
        self.status_label.config(text=timer.status, fg=self._status_colour())

        if timer.running:
            self.countdown_label.config(text=timer.format_remaining())
            total = timer.work_seconds if timer.phase is Phase.WORK else timer.break_seconds
            done = 1000 * (1 - timer.remaining / total) if total else 0
            self.progress["value"] = max(0, min(1000, done))
        else:
            self.countdown_label.config(text="--:--")
            self.progress["value"] = 0

        stats = timer.stats
        self.stats_label.config(
            text=(
                f"Отработано      {timer.format_worked()}\n"
                f"Перерывов       {stats.breaks_taken}\n"
                f"Напоминаний     {stats.blink_reminders}\n"
                f"Пауз            {stats.pauses_count}"
            )
        )

    def _status_colour(self) -> str:
        if not self.timer.running:
            return COLORS["stopped"]
        if self.timer.paused:
            return COLORS["paused"]
        if self.timer.phase is Phase.BREAK:
            return COLORS["break"]
        return COLORS["work"]

    def _refresh_buttons(self) -> None:
        running = self.timer.running
        self.start_button.config(state="disabled" if running else "normal")
        self.pause_button.config(
            state="normal" if running else "disabled",
            text="▶ Продолжить" if self.timer.paused else "⏸ Пауза",
        )
        self.stop_button.config(state="normal" if running else "disabled")
        self.skip_button.config(
            state="normal" if self.timer.phase is Phase.BREAK else "disabled"
        )

    def _refresh_history(self) -> None:
        rows = storage.daily_report(limit=3)
        if not rows:
            self.history_label.config(text="История появится после первого сеанса")
            return
        lines = []
        for row in rows:
            seconds = int(row["worked_seconds"])
            lines.append(
                f"{row['date']}   {seconds // 3600}ч {(seconds % 3600) // 60:02d}м"
                f"   перерывов: {row['breaks_taken']}"
            )
        self.history_label.config(text="Последние дни:\n" + "\n".join(lines))

    def show_banner(self, text: str, colour: str) -> None:
        self.banner.config(text=text, bg=colour)

    # ================================================================

    def on_close(self) -> None:
        if self.timer.running and self.started_at is not None:
            storage.append_session(
                self.timer.stats.as_dict(), self.started_at, datetime.now()
            )
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    WorkTimerApp().run()
    return 0


if __name__ == "__main__":
    # Раньше здесь создавался объект окна без вызова run(): программа
    # запускалась и тут же закрывалась, не показав ничего.
    raise SystemExit(main())
