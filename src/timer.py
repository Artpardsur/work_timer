"""Двигатель таймера: считает время и сообщает, когда пора моргнуть или встать.

Здесь нет ни потоков, ни sleep, ни интерфейса. Всё состояние меняется в
:meth:`WorkTimer.tick`, который вызывает интерфейс — консольный из своего цикла,
оконный из ``root.after``. Благодаря этому таймер проверяется тестами с
подставными часами: сорок минут работы прогоняются за миллисекунды.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List

# Ноутбук могли закрыть на час. Без ограничения после пробуждения посыпалась бы
# сотня пропущенных напоминаний подряд.
MAX_TICK_SECONDS = 60.0


class Phase(str, Enum):
    """Чем занят таймер прямо сейчас."""

    IDLE = "idle"
    WORK = "work"
    BREAK = "break"


class Event(str, Enum):
    """О чём таймер сообщает интерфейсу."""

    BLINK = "blink"              # пора моргнуть
    BREAK_START = "break_start"  # пора встать и размяться
    BREAK_END = "break_end"      # перерыв закончился


@dataclass
class Stats:
    """Накопленные за сеанс числа."""

    breaks_taken: int = 0
    blink_reminders: int = 0
    pauses_count: int = 0
    worked_seconds: float = 0.0
    rested_seconds: float = 0.0

    def as_dict(self) -> dict:
        return {
            "breaks_taken": self.breaks_taken,
            "blink_reminders": self.blink_reminders,
            "pauses_count": self.pauses_count,
            "worked_seconds": round(self.worked_seconds, 1),
            "rested_seconds": round(self.rested_seconds, 1),
        }


@dataclass
class WorkTimer:
    """Чередование работы и перерывов с напоминаниями о моргании.

    Аргументы задаются в минутах и могут быть дробными — 0.5 удобно для
    проверки, не дожидаясь получаса.
    """

    work_minutes: float = 30.0
    blink_minutes: float = 10.0
    break_minutes: float = 5.0
    clock: Callable[[], float] = time.monotonic

    phase: Phase = field(default=Phase.IDLE, init=False)
    paused: bool = field(default=False, init=False)
    stats: Stats = field(default_factory=Stats, init=False)

    _phase_elapsed: float = field(default=0.0, init=False)
    _blink_elapsed: float = field(default=0.0, init=False)
    _last_tick: float = field(default=0.0, init=False)

    # --- управление -----------------------------------------------------

    @property
    def running(self) -> bool:
        return self.phase is not Phase.IDLE

    def start(self) -> None:
        """Начать сеанс с чистого листа."""
        self.phase = Phase.WORK
        self.paused = False
        self.stats = Stats()
        self._phase_elapsed = 0.0
        self._blink_elapsed = 0.0
        self._last_tick = self.clock()

    def pause(self) -> None:
        if self.running and not self.paused:
            self.paused = True
            self.stats.pauses_count += 1

    def resume(self) -> None:
        if self.running and self.paused:
            self.paused = False
            # Время паузы не должно попасть в отработанное: сдвигаем точку
            # отсчёта, иначе следующий tick засчитает всю паузу как работу.
            self._last_tick = self.clock()

    def toggle_pause(self) -> None:
        if self.paused:
            self.resume()
        else:
            self.pause()

    def stop(self) -> None:
        self.phase = Phase.IDLE
        self.paused = False
        self._phase_elapsed = 0.0
        self._blink_elapsed = 0.0

    def skip_break(self) -> None:
        """Досрочно вернуться к работе."""
        if self.phase is Phase.BREAK:
            self._start_work()

    # --- ход времени -----------------------------------------------------

    def tick(self) -> List[Event]:
        """Продвинуть таймер и вернуть накопившиеся события.

        Вызывать как угодно часто: интервалы считаются по часам, а не по
        числу вызовов, поэтому раз в секунду и раз в 100 мс дадут одно и то же.
        """
        now = self.clock()
        delta = min(max(0.0, now - self._last_tick), MAX_TICK_SECONDS)
        self._last_tick = now

        if not self.running or self.paused or delta == 0.0:
            return []

        self._phase_elapsed += delta
        events: List[Event] = []

        if self.phase is Phase.WORK:
            self.stats.worked_seconds += delta
            self._blink_elapsed += delta

            while self.blink_seconds > 0 and self._blink_elapsed >= self.blink_seconds:
                self._blink_elapsed -= self.blink_seconds
                self.stats.blink_reminders += 1
                events.append(Event.BLINK)

            if self._phase_elapsed >= self.work_seconds:
                self.phase = Phase.BREAK
                self._phase_elapsed = 0.0
                self.stats.breaks_taken += 1
                events.append(Event.BREAK_START)
        else:
            self.stats.rested_seconds += delta
            if self._phase_elapsed >= self.break_seconds:
                self._start_work()
                events.append(Event.BREAK_END)

        return events

    def _start_work(self) -> None:
        self.phase = Phase.WORK
        self._phase_elapsed = 0.0
        self._blink_elapsed = 0.0

    # --- то, что показывает интерфейс -------------------------------------

    @property
    def work_seconds(self) -> float:
        return self.work_minutes * 60

    @property
    def blink_seconds(self) -> float:
        return self.blink_minutes * 60

    @property
    def break_seconds(self) -> float:
        return self.break_minutes * 60

    @property
    def remaining(self) -> float:
        """Сколько секунд осталось до конца текущей фазы."""
        if not self.running:
            return 0.0
        total = self.work_seconds if self.phase is Phase.WORK else self.break_seconds
        return max(0.0, total - self._phase_elapsed)

    @property
    def status(self) -> str:
        if not self.running:
            return "⏹ Остановлен"
        if self.paused:
            return "⏸ На паузе"
        if self.phase is Phase.BREAK:
            return "🧘 Перерыв"
        return "▶ Работа"

    def format_remaining(self) -> str:
        seconds = int(self.remaining)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def format_worked(self) -> str:
        seconds = int(self.stats.worked_seconds)
        return f"{seconds // 3600}ч {(seconds % 3600) // 60:02d}м"
