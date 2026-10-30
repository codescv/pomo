"""Persistence for daily completed Pomodoro statistics."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

APP_DIR = Path.home() / ".pomo"
STATS_FILE = APP_DIR / "stats.json"


def ensure_app_dir() -> Path:
    """Ensure the ~/.pomo directory exists."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return APP_DIR


def _load_stats() -> dict[str, int]:
    """Load the daily stats mapping (YYYY-MM-DD -> count)."""
    if not STATS_FILE.exists():
        return {}
    try:
        data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                str(k): int(v)
                for k, v in data.items()
                if isinstance(v, (int, float))
            }
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _save_stats(stats: dict[str, int]) -> None:
    """Atomically write the daily stats mapping to ~/.pomo/stats.json."""
    ensure_app_dir()
    tmp_file = STATS_FILE.with_suffix(".tmp")
    tmp_file.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_file.replace(STATS_FILE)


def get_today_count() -> int:
    """Return the number of completed Pomodoros today."""
    today_key = date.today().isoformat()
    stats = _load_stats()
    return stats.get(today_key, 0)


def increment_today_count() -> int:
    """Increment today's completed Pomodoro count and return the updated value."""
    today_key = date.today().isoformat()
    stats = _load_stats()
    new_count = stats.get(today_key, 0) + 1
    stats[today_key] = new_count
    _save_stats(stats)
    return new_count
