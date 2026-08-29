"""Консольный интерфейс: живой обратный отсчёт плюс команды с клавиатуры.

Отсчёт идёт в главном потоке, а ввод читается отдельным — иначе ``input()``
замораживал бы таймер до нажатия Enter.
"""

from __future__ import annotations

import queue
import sys
import threading
from datetime import datetime

from src import notify, storage
from src.timer import Event, WorkTimer

TICK_SECONDS = 0.25

HELP = """
Команды (ввести и нажать Enter):
  p  — пауза / продолжить
  s  — стоп / старт заново
  r  — отчёт по дням
  h  — эта справка
  q  — выход
"""


def make_output_safe() -> None:
    """Не падать, если консоль не умеет эмодзи.

    В обычном окне Windows всё выводится нормально, но стоит перенаправить
    вывод в файл или в другую программу — и Python берёт кодировку системы
    (cp1251), где эмодзи нет. Без этой страховки программа падала на первой
    же строке заголовка.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):
            pass


def read_commands(commands: "queue.Queue[str]") -> None:
    """Поток чтения клавиатуры."""
    while True:
        try:
            line = sys.stdin.readline()
        except (ValueError, OSError):
            return
        if not line:
            commands.put("q")
            return
        commands.put(line.strip().lower())


def print_report() -> None:
    rows = storage.daily_report()
    print()
    if not rows:
        print("  История пока пуста — она появится после первого завершённого сеанса.")
        return
    print("  Дата         Отработано   Перерывов   Сеансов")
    for row in rows:
        seconds = int(row["worked_seconds"])
        worked = f"{seconds // 3600}ч {(seconds % 3600) // 60:02d}м"
        print(f"  {row['date']}   {worked:>10}   {row['breaks_taken']:>9}   {row['sessions']:>7}")
    print()


def handle_event(event: Event, settings: dict) -> None:
    key = event.value
    title, text = notify.message(key)
    print(f"\n  {title} — {text}")
    if settings.get("sound", True):
        notify.play(key, use_long_blink=settings.get("long_blink_sound", False))


def main() -> int:
    make_output_safe()
    settings = storage.load_settings()
    timer = WorkTimer(
        work_minutes=float(settings["work_minutes"]),
        blink_minutes=float(settings["blink_minutes"]),
        break_minutes=float(settings["break_minutes"]),
    )

    print("=" * 58)
    print("  🧘 WORK TIMER — напоминания о перерывах и о моргании")
    print("=" * 58)
    print(
        f"  Перерыв каждые {timer.work_minutes:g} мин, "
        f"моргать каждые {timer.blink_minutes:g} мин, "
        f"отдых {timer.break_minutes:g} мин."
    )
    print(HELP)

    commands: "queue.Queue[str]" = queue.Queue()
    threading.Thread(target=read_commands, args=(commands,), daemon=True).start()

    timer.start()
    started_at = datetime.now()

    try:
        while True:
            for event in timer.tick():
                handle_event(event, settings)

            line = f"  {timer.status}  осталось {timer.format_remaining()}  |  за сеанс: {timer.format_worked()}"
            print(line.ljust(72), end="\r", flush=True)

            try:
                command = commands.get(timeout=TICK_SECONDS)
            except queue.Empty:
                continue

            print()
            if command == "p":
                timer.toggle_pause()
                print(f"  {timer.status}")
            elif command == "s":
                if timer.running:
                    storage.append_session(
                        timer.stats.as_dict(), started_at, datetime.now()
                    )
                    timer.stop()
                    print("  Сеанс записан в историю.")
                else:
                    timer.start()
                    started_at = datetime.now()
                    print("  Поехали.")
            elif command == "r":
                print_report()
            elif command == "h":
                print(HELP)
            elif command == "q":
                break
            elif command:
                print("  Не понял команду. Наберите h для справки.")
    except KeyboardInterrupt:
        pass

    if timer.running:
        storage.append_session(timer.stats.as_dict(), started_at, datetime.now())
    print()
    print(f"  Итог: {timer.format_worked()} работы, "
          f"{timer.stats.breaks_taken} перерывов, "
          f"{timer.stats.blink_reminders} напоминаний о моргании.")
    print("  Будьте здоровы!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
