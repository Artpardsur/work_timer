"""Проверки двигателя таймера на подставных часах.

Настоящие полчаса ждать не нужно: часы двигаются вручную, поэтому целый
рабочий день проверяется за миллисекунды.
"""

import pytest

from src.timer import Event, Phase, WorkTimer


class FakeClock:
    """Часы, которые идут только когда их просят."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def timer(clock):
    # Мелкие интервалы: работа 10 с, моргание каждые 4 с, отдых 3 с.
    instance = WorkTimer(
        work_minutes=10 / 60, blink_minutes=4 / 60, break_minutes=3 / 60, clock=clock
    )
    instance.start()
    return instance


def run(timer, clock, seconds, step=1.0):
    """Прогнать столько-то секунд и собрать все события."""
    events = []
    remaining = seconds
    while remaining > 0:
        move = min(step, remaining)
        clock.advance(move)
        events.extend(timer.tick())
        remaining -= move
    return events


def test_starts_in_work_phase(timer):
    assert timer.phase is Phase.WORK
    assert timer.running


def test_blink_reminder_fires_on_schedule(timer, clock):
    assert run(timer, clock, 3) == []
    assert run(timer, clock, 1) == [Event.BLINK]


def test_break_starts_when_work_period_ends(timer, clock):
    events = run(timer, clock, 10)
    assert Event.BREAK_START in events
    assert timer.phase is Phase.BREAK


def test_break_ends_and_work_resumes(timer, clock):
    run(timer, clock, 10)
    events = run(timer, clock, 3)
    assert Event.BREAK_END in events
    assert timer.phase is Phase.WORK


def test_pause_actually_stops_the_countdown(timer, clock):
    """Главная поломка прежней версии: пауза не останавливала отсчёт."""
    run(timer, clock, 4)
    remaining_before = timer.remaining

    timer.pause()
    clock.advance(600)          # десять минут в паузе
    assert timer.tick() == []

    assert timer.remaining == pytest.approx(remaining_before)
    assert timer.stats.worked_seconds == pytest.approx(4)


def test_pause_does_not_leak_into_worked_time(timer, clock):
    run(timer, clock, 2)
    timer.pause()
    clock.advance(300)
    timer.resume()
    run(timer, clock, 2)

    assert timer.stats.worked_seconds == pytest.approx(4)


def test_pause_is_counted_in_stats(timer):
    timer.pause()
    timer.pause()               # повторная пауза ничего не добавляет
    assert timer.stats.pauses_count == 1


def test_stop_leaves_no_running_state(timer, clock):
    run(timer, clock, 5)
    timer.stop()
    assert not timer.running
    assert timer.remaining == 0
    assert timer.tick() == []


def test_skip_break_returns_to_work(timer, clock):
    run(timer, clock, 10)
    assert timer.phase is Phase.BREAK

    timer.skip_break()

    assert timer.phase is Phase.WORK
    assert timer.remaining == pytest.approx(timer.work_seconds)


def test_long_sleep_does_not_flood_with_reminders(timer, clock):
    """После закрытой крышки ноутбука не должно посыпаться сто напоминаний."""
    clock.advance(3600)
    events = timer.tick()
    assert events.count(Event.BLINK) <= 15


def test_tick_rate_does_not_change_the_result(clock):
    """Раз в секунду и раз в сотую секунды должны дать одно и то же."""
    coarse = WorkTimer(work_minutes=1, blink_minutes=0.25, break_minutes=0.5, clock=clock)
    coarse.start()
    # 61 секунда, а не ровно 60: на точной границе накопленная погрешность
    # мелкого шага решает исход, и сравнивать там нечего.
    coarse_events = run(coarse, clock, 61, step=1.0)

    fine_clock = FakeClock()
    fine = WorkTimer(work_minutes=1, blink_minutes=0.25, break_minutes=0.5, clock=fine_clock)
    fine.start()
    fine_events = run(fine, fine_clock, 61, step=0.01)

    assert coarse_events == fine_events
    assert coarse.stats.blink_reminders == fine.stats.blink_reminders


def test_worked_time_is_formatted_for_humans(timer, clock):
    run(timer, clock, 10, step=1.0)
    timer.stats.worked_seconds = 3 * 3600 + 25 * 60
    assert timer.format_worked() == "3ч 25м"


def test_status_reflects_phase(timer, clock):
    assert "Работа" in timer.status
    timer.pause()
    assert "паузе" in timer.status
    timer.resume()
    run(timer, clock, 10)
    assert "Перерыв" in timer.status
    timer.stop()
    assert "Остановлен" in timer.status
