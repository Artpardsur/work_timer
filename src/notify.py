"""Уведомления: звук и текст.

Звук проигрывается средствами системы, без сторонних библиотек. Прежняя
зависимость ``playsound==1.3.0`` собирается не на всех машинах и тянула за
собой лишний шаг установки — на Windows ровно то же делает встроенный winsound.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def _sounds_dir() -> Path:
    """Папка со звуками — своя у обычного запуска и у собранного exe."""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled) / "sounds"
    return Path(__file__).resolve().parent.parent / "sounds"


SOUNDS_DIR = _sounds_dir()

# blink.wav в комплекте длится 36,8 секунды — это не короткий сигнал, а целый
# фрагмент. Каждые десять минут это утомляет, поэтому по умолчанию напоминание
# о моргании — короткий системный звук. Включается в настройках.
SOUND_FILES = {
    "blink": None,
    "break_start": SOUNDS_DIR / "break_start.wav",
    "break_end": SOUNDS_DIR / "break_end.wav",
}

LONG_BLINK_SOUND = SOUNDS_DIR / "blink.wav"


def beep() -> None:
    """Короткий системный сигнал."""
    if sys.platform == "win32":
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return
        except (ImportError, RuntimeError):
            pass
    print("\a", end="", flush=True)


def play(sound_key: str, use_long_blink: bool = False) -> None:
    """Проиграть звук события, не блокируя программу.

    Если файла нет или система не умеет его играть — просто пикнет.
    """
    path: Optional[Path] = SOUND_FILES.get(sound_key)
    if sound_key == "blink" and use_long_blink:
        path = LONG_BLINK_SOUND

    if path is None or not path.is_file():
        beep()
        return

    if sys.platform == "win32":
        try:
            import winsound

            winsound.PlaySound(
                str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            )
            return
        except (ImportError, RuntimeError):
            pass
    beep()


MESSAGES = {
    "blink": ("👁 Моргните", "Оторвитесь от экрана и посмотрите вдаль 20 секунд."),
    "break_start": ("🧘 Перерыв", "Встаньте и разомнитесь."),
    "break_end": ("✅ Перерыв закончен", "Возвращайтесь к работе."),
}


def message(sound_key: str) -> tuple:
    """Заголовок и текст для события."""
    return MESSAGES.get(sound_key, ("Work Timer", ""))
