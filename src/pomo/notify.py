"""macOS native notification and system sound helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

OSASCRIPT_BIN = Path("/usr/bin/osascript")
AFPLAY_BIN = Path("/usr/bin/afplay")
GLASS_SOUND = Path("/System/Library/Sounds/Glass.aiff")


def notify_completion(today_count: int) -> None:
    """Send a macOS native notification banner and play the Glass system chime."""
    safe_count = int(today_count)
    script = (
        f'display notification "25 分钟专注已结束，起来活动一下吧（今日已完成 {safe_count} 🍅）" '
        'with title "🍅 专注完成！" sound name "Glass"'
    )

    if OSASCRIPT_BIN.exists():
        try:
            subprocess.Popen(
                [str(OSASCRIPT_BIN), "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass

    if AFPLAY_BIN.exists() and GLASS_SOUND.exists():
        try:
            subprocess.Popen(
                [str(AFPLAY_BIN), str(GLASS_SOUND)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
