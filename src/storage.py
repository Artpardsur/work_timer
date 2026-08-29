"""Настройки и история сеансов.

Всё лежит в системной папке приложения, а не рядом с программой: так данные
переживают переустановку и не мешаются в репозитории.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

APP_NAME = "WorkTimer"

DEFAULT_SETTINGS = {
    "work_minutes": 30.0,
    "blink_minutes": 10.0,
    "break_minutes": 5.0,
    "sound": True,
    "long_blink_sound": False,
}


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / APP_NAME


def settings_file() -> Path:
    return data_dir() / "settings.json"


def sessions_file() -> Path:
    return data_dir() / "sessions.json"


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
    except OSError:
        return False


# --- настройки ---------------------------------------------------------


def load_settings() -> Dict:
    settings = dict(DEFAULT_SETTINGS)
    stored = _read_json(settings_file(), {})
    if isinstance(stored, dict):
        # Берём только знакомые ключи: чужой мусор в файле не должен
        # добираться до конструктора таймера.
        for key in DEFAULT_SETTINGS:
            if key in stored:
                settings[key] = stored[key]
    return settings


def save_settings(settings: Dict) -> bool:
    return _write_json(settings_file(), settings)


# --- история -----------------------------------------------------------


def append_session(stats: Dict, started_at: datetime, ended_at: datetime) -> bool:
    """Дописать завершённый сеанс в историю."""
    sessions = load_sessions()
    sessions.append(
        {
            "date": started_at.strftime("%Y-%m-%d"),
            "started": started_at.strftime("%H:%M"),
            "ended": ended_at.strftime("%H:%M"),
            **stats,
        }
    )
    # Держим последние 500 записей: файл не должен расти бесконечно.
    return _write_json(sessions_file(), sessions[-500:])


def load_sessions() -> List[Dict]:
    sessions = _read_json(sessions_file(), [])
    return sessions if isinstance(sessions, list) else []


def daily_report(limit: int = 7) -> List[Dict]:
    """Сводка по дням, свежие сверху."""
    by_day: Dict[str, Dict] = defaultdict(
        lambda: {"worked_seconds": 0.0, "breaks_taken": 0, "sessions": 0}
    )
    for session in load_sessions():
        day = by_day[session.get("date", "?")]
        day["worked_seconds"] += float(session.get("worked_seconds", 0))
        day["breaks_taken"] += int(session.get("breaks_taken", 0))
        day["sessions"] += 1

    rows = [{"date": date, **values} for date, values in by_day.items()]
    rows.sort(key=lambda row: row["date"], reverse=True)
    return rows[:limit]
