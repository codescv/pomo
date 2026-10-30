"""macOS top menu bar Pomodoro application built with rumps."""

from __future__ import annotations

import math
import time
from datetime import date
from typing import Callable

import AppKit
import rumps

from pomo.icons import ensure_template_icons
from pomo.notify import notify_completion
from pomo.stats import get_today_count, increment_today_count

POMO_MINUTES = 25
POMO_DURATION_SECONDS = POMO_MINUTES * 60

STATE_IDLE = "IDLE"
STATE_RUNNING = "RUNNING"
STATE_PAUSED = "PAUSED"


def _hide_dock_icon() -> None:
    """Configure macOS NSApplication as an Accessory app (menu bar only, no Dock icon)."""
    try:
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except Exception:
        pass


class PomoApp(rumps.App):
    """Minimalist 25-minute single countdown Pomodoro timer in the macOS menu bar."""

    def __init__(self, on_exit: Callable[[], None] | None = None) -> None:
        _hide_dock_icon()
        self._tomato_icon, self._paused_icon = ensure_template_icons()
        super().__init__(
            name="Pomo",
            title=None,
            icon=self._tomato_icon,
            template=True,
            quit_button=None,
        )

        self._on_exit = on_exit
        self.state: str = STATE_IDLE
        self.remaining_seconds: float = float(POMO_DURATION_SECONDS)
        self.end_time: float = 0.0
        self._last_date: str = date.today().isoformat()

        self.start_pause_item = rumps.MenuItem(
            f"开始专注 ({POMO_MINUTES}分钟)",
            callback=self.toggle_timer,
        )
        self.reset_item = rumps.MenuItem("重置", callback=None)
        self.stats_item = rumps.MenuItem(
            self._format_stats_title(get_today_count()),
            callback=None,
        )
        self.stats_item.set_icon(self._tomato_icon, dimensions=(16, 16), template=True)
        self.quit_item = rumps.MenuItem("退出", callback=self.quit_app)

        self.menu = [
            self.start_pause_item,
            self.reset_item,
            None,
            self.stats_item,
            None,
            self.quit_item,
        ]

        self.timer = rumps.Timer(self._on_tick, 1)
        self.timer.start()

    @staticmethod
    def _format_stats_title(count: int) -> str:
        return f"今日完成: {count}"

    @staticmethod
    def _format_minutes(seconds: float) -> int:
        return max(1, math.ceil(seconds / 60.0))

    def _refresh_daily_stats_if_needed(self) -> None:
        today_str = date.today().isoformat()
        if today_str != self._last_date:
            self._last_date = today_str
            self.stats_item.title = self._format_stats_title(get_today_count())

    def _update_ui(self) -> None:
        """Synchronize the menu bar template icon, title, and dropdown item states."""
        if self.state == STATE_IDLE:
            if self.icon != self._tomato_icon:
                self.icon = self._tomato_icon
            if self.title is not None:
                self.title = None
            self.start_pause_item.title = f"开始专注 ({POMO_MINUTES}分钟)"
            self.reset_item.set_callback(None)
        elif self.state == STATE_RUNNING:
            if self.icon != self._tomato_icon:
                self.icon = self._tomato_icon
            mins = self._format_minutes(self.remaining_seconds)
            new_title = f"{mins}m"
            if self.title != new_title:
                self.title = new_title
            self.start_pause_item.title = "暂停"
            if self.reset_item.callback is None:
                self.reset_item.set_callback(self.reset_timer)
        elif self.state == STATE_PAUSED:
            if self.icon != self._paused_icon:
                self.icon = self._paused_icon
            mins = self._format_minutes(self.remaining_seconds)
            new_title = f"{mins}m"
            if self.title != new_title:
                self.title = new_title
            self.start_pause_item.title = "继续"
            if self.reset_item.callback is None:
                self.reset_item.set_callback(self.reset_timer)

    def toggle_timer(self, _: rumps.MenuItem) -> None:
        """Handle clicks on Start / Pause / Resume."""
        self._refresh_daily_stats_if_needed()

        if self.state == STATE_IDLE:
            self.remaining_seconds = float(POMO_DURATION_SECONDS)
            self.end_time = time.monotonic() + self.remaining_seconds
            self.state = STATE_RUNNING
        elif self.state == STATE_RUNNING:
            self.remaining_seconds = max(0.0, self.end_time - time.monotonic())
            self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            self.end_time = time.monotonic() + self.remaining_seconds
            self.state = STATE_RUNNING

        self._update_ui()

    def reset_timer(self, _: rumps.MenuItem) -> None:
        """Reset the current Pomodoro countdown back to idle."""
        self._refresh_daily_stats_if_needed()
        self.state = STATE_IDLE
        self.remaining_seconds = float(POMO_DURATION_SECONDS)
        self.end_time = 0.0
        self._update_ui()

    def _on_tick(self, _: rumps.Timer) -> None:
        """Periodic 1-second callback to update countdown and check completion."""
        self._refresh_daily_stats_if_needed()

        if self.state != STATE_RUNNING:
            return

        remaining = self.end_time - time.monotonic()
        if remaining <= 0:
            self.state = STATE_IDLE
            self.remaining_seconds = float(POMO_DURATION_SECONDS)
            self.end_time = 0.0
            self._update_ui()

            today_count = increment_today_count()
            self._last_date = date.today().isoformat()
            self.stats_item.title = self._format_stats_title(today_count)
            notify_completion(today_count)
        else:
            self.remaining_seconds = remaining
            self._update_ui()

    def quit_app(self, _: rumps.MenuItem) -> None:
        """Clean up and quit the menu bar application."""
        self.timer.stop()
        if self._on_exit is not None:
            self._on_exit()
        rumps.quit_application()


def run_menubar_app(on_exit: Callable[[], None] | None = None) -> None:
    """Entry point to launch the menu bar Pomodoro timer."""
    _hide_dock_icon()
    app = PomoApp(on_exit=on_exit)
    app.run()
