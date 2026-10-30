"""Command-line interface for Pomo (background daemon, foreground, status, and optional .app helper)."""

from __future__ import annotations

import argparse
import atexit
import os
import plistlib
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

from pomo import __version__
from pomo.stats import APP_DIR, ensure_app_dir, get_today_count

PID_FILE = APP_DIR / "pomo.pid"
LOG_FILE = APP_DIR / "pomo.log"
DEFAULT_APP_BUNDLE = Path.home() / "Applications" / "Pomo.app"


def _read_running_pid() -> int | None:
    """Return the PID of the running Pomo instance if alive, else None."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def _write_pid(pid: int) -> None:
    ensure_app_dir()
    PID_FILE.write_text(f"{pid}\n", encoding="utf-8")


def _cleanup_pid() -> None:
    """Remove PID file if it belongs to the current process."""
    try:
        if PID_FILE.exists():
            recorded = int(PID_FILE.read_text(encoding="utf-8").strip())
            if recorded == os.getpid():
                PID_FILE.unlink(missing_ok=True)
    except (ValueError, OSError):
        pass


def cmd_start() -> int:
    """Start Pomo in the background and return control to the terminal immediately."""
    existing_pid = _read_running_pid()
    if existing_pid is not None:
        print(f"🍅 Pomo 已在顶部任务栏运行中 (PID: {existing_pid})")
        print(f"📊 今日完成: {get_today_count()} 🍅")
        return 0

    ensure_app_dir()
    with LOG_FILE.open("a", encoding="utf-8") as log_fp:
        proc = subprocess.Popen(
            [sys.executable, "-m", "pomo.cli", "fg"],
            stdin=subprocess.DEVNULL,
            stdout=log_fp,
            stderr=log_fp,
            start_new_session=True,
        )

    time.sleep(0.3)
    if proc.poll() is not None:
        print(f"❌ Pomo 启动失败，请检查日志: {LOG_FILE}", file=sys.stderr)
        return 1

    _write_pid(proc.pid)
    print(f"🍅 Pomo 已在后台启动 (PID: {proc.pid})，请查看屏幕顶部任务栏！")
    print("💡 提示: 运行 'pomo stop' 可停止后台进程，运行 'pomo status' 可查看状态。")
    return 0


def cmd_fg() -> int:
    """Run Pomo menu bar app in the foreground."""
    existing_pid = _read_running_pid()
    if existing_pid is not None and existing_pid != os.getpid():
        print(f"🍅 Pomo 已在运行中 (PID: {existing_pid})", file=sys.stderr)
        return 0

    _write_pid(os.getpid())
    atexit.register(_cleanup_pid)

    def _handle_sigterm(signum: int, frame: object) -> None:
        _cleanup_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    from pomo.app import run_menubar_app

    run_menubar_app(on_exit=_cleanup_pid)
    return 0


def cmd_stop() -> int:
    """Stop the running background Pomo process."""
    pid = _read_running_pid()
    if pid is None:
        print("ℹ️ Pomo 当前未在运行。")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    for _ in range(20):
        try:
            os.kill(pid, 0)
            time.sleep(0.1)
        except OSError:
            break

    PID_FILE.unlink(missing_ok=True)
    print(f"🛑 已停止 Pomo 后台进程 (PID: {pid})")
    return 0


def cmd_status() -> int:
    """Print current daemon status and today's completed Pomodoro count."""
    pid = _read_running_pid()
    count = get_today_count()
    if pid is not None:
        print(f"🟢 状态: 运行中 (PID: {pid})")
    else:
        print("⚪ 状态: 未运行")
    print(f"📊 今日完成: {count} 🍅")
    return 0


def cmd_install_app() -> int:
    """Generate a lightweight ~/Applications/Pomo.app wrapper around the uv environment."""
    contents_dir = DEFAULT_APP_BUNDLE / "Contents"
    macos_dir = contents_dir / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)

    info_plist = {
        "CFBundleName": "Pomo",
        "CFBundleDisplayName": "Pomo",
        "CFBundleIdentifier": "com.chii.pomo",
        "CFBundleVersion": __version__,
        "CFBundleShortVersionString": __version__,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "pomo-launcher",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    }
    with (contents_dir / "Info.plist").open("wb") as fp:
        plistlib.dump(info_plist, fp)

    launcher_path = macos_dir / "pomo-launcher"
    python_bin = Path(sys.executable).resolve()
    launcher_script = f"""#!/bin/sh
exec "{python_bin}" -m pomo.cli fg
"""
    launcher_path.write_text(launcher_script, encoding="utf-8")
    launcher_path.chmod(
        launcher_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )

    print(f"✅ 已生成轻量级 macOS 应用: {DEFAULT_APP_BUNDLE}")
    print("💡 该应用直接调用本地 uv Python 环境，不含外部未签名二进制，不会被公司 Gatekeeper 拦截。")
    print("   你现在可以通过 Spotlight / 聚焦搜索 'Pomo' 启动，或将其加入「登录项」开机自启。")
    return 0


def cmd_uninstall_app() -> int:
    """Remove ~/Applications/Pomo.app if present."""
    if DEFAULT_APP_BUNDLE.exists():
        shutil.rmtree(DEFAULT_APP_BUNDLE)
        print(f"🗑️ 已移除应用: {DEFAULT_APP_BUNDLE}")
    else:
        print(f"ℹ️ 未找到已安装的应用 ({DEFAULT_APP_BUNDLE})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pomo",
        description="🍅 极简 macOS 顶部任务栏番茄钟 (25分钟单次专注倒计时)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("start", help="在后台启动顶部任务栏番茄钟（默认行为）")
    subparsers.add_parser("stop", help="停止后台运行的番茄钟")
    subparsers.add_parser("fg", help="在前台运行番茄钟（阻塞当前终端）")
    subparsers.add_parser("status", help="查看运行状态与今日完成番茄数")
    subparsers.add_parser(
        "install-app",
        help="可选：在 ~/Applications 生成免签名的 Pomo.app 快捷启动应用",
    )
    subparsers.add_parser(
        "uninstall-app",
        help="移除 ~/Applications/Pomo.app",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command or "start"

    if cmd == "start":
        return cmd_start()
    if cmd == "stop":
        return cmd_stop()
    if cmd == "fg":
        return cmd_fg()
    if cmd == "status":
        return cmd_status()
    if cmd == "install-app":
        return cmd_install_app()
    if cmd == "uninstall-app":
        return cmd_uninstall_app()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
