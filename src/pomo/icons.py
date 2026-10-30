"""Monochrome macOS template icon generator and asset resolver."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
TOMATO_ICON_PATH = ASSETS_DIR / "tomato_template.png"
TOMATO_PAUSED_ICON_PATH = ASSETS_DIR / "tomato_paused_template.png"


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = _clamp((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _sd_segment(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    pax, pay = px - ax, py - ay
    bax, bay = bx - ax, by - ay
    h = _clamp((pax * bax + pay * bay) / (bax * bax + bay * bay + 1e-9))
    return math.hypot(pax - bax * h, pay - bay * h)


def _sd_calyx(x: float, y: float) -> float:
    ax = abs(x)
    d_stem = _sd_segment(x, y, 0.0, -0.40, 0.05, -0.78) - 0.075
    d_leaf1 = _sd_segment(ax, y, 0.0, -0.40, 0.24, -0.52) - 0.068
    d_leaf2 = _sd_segment(ax, y, 0.24, -0.52, 0.46, -0.42) - 0.058
    d_inner = _sd_segment(ax, y, 0.0, -0.40, 0.18, -0.30) - 0.062
    return min(d_stem, d_leaf1, d_leaf2, d_inner)


def _sd_tomato_body(x: float, y: float) -> float:
    cy = 0.15 + 0.04 * math.exp(-((x / 0.28) ** 2)) * (1.0 if y < 0.15 else 0.0)
    rx = 0.68 - 0.03 * (y - 0.15)
    ry = 0.56
    r = math.hypot(x / rx, (y - cy) / ry)
    return (r - 1.0) * min(rx, ry)


def _tomato_alpha(u: float, v: float, paused: bool = False) -> float:
    aa = 2.2 / 80.0
    d_calyx = _sd_calyx(u, v)
    d_body = _sd_tomato_body(u, v)
    d_body_cut = max(d_body, -(d_calyx - 0.075))

    if paused:
        bar_x = abs(u) - 0.145
        d_bar = _sd_segment(bar_x, v, 0.0, -0.02, 0.0, 0.34) - 0.065
        d_body_cut = max(d_body_cut, -d_bar)
    else:
        dx = u - (-0.02)
        dy = (v - 0.15) * 1.15
        ang = math.atan2(dy, dx)
        if ang < 0:
            ang += 2.0 * math.pi
        t_ang = _clamp(ang, 2.65, 3.48)
        cx = -0.02 + 0.44 * math.cos(t_ang)
        cy = 0.15 + (0.44 * math.sin(t_ang)) / 1.15
        d_shine = math.hypot(u - cx, v - cy) - 0.048
        d_body_cut = max(d_body_cut, -d_shine)

    d = min(d_calyx, d_body_cut)
    return 1.0 - _smoothstep(-aa, aa, d)


def _write_template_png(path: Path, paused: bool = False, size: int = 80) -> None:
    """Write an 80x80 (@4x for 20pt) macOS monochrome template PNG (black + alpha)."""
    half = size / 2.0
    scale = half * 1.06
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        v = (y + 0.5 - half) / scale - 0.06
        for x in range(size):
            u = (x + 0.5 - half) / scale
            a = int(round(_tomato_alpha(u, v, paused=paused) * 255.0))
            raw.extend((0, 0, 0, a))

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def ensure_template_icons(force: bool = False) -> tuple[str, str]:
    """Ensure the normal and paused monochrome template icons exist on disk."""
    if force or not TOMATO_ICON_PATH.exists():
        _write_template_png(TOMATO_ICON_PATH, paused=False)
    if force or not TOMATO_PAUSED_ICON_PATH.exists():
        _write_template_png(TOMATO_PAUSED_ICON_PATH, paused=True)
    return str(TOMATO_ICON_PATH), str(TOMATO_PAUSED_ICON_PATH)
