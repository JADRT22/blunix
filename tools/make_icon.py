"""Gera o ícone do Blunix.

Estratégia: usar o ícone oficial do Sober como BASE (duas barras arredondadas
em diagonal, composição que preenche o tile inteiro) e recolorir o gradiente
verde para o azul elétrico → ciano do Blunix. O resultado fica com a mesma
silhueta do Sober (fácil de reconhecer) e aparece maior na taskbar/dock.

Requer GdkPixbuf (presente em qualquer sistema com GTK). Se o ícone do Sober
não for encontrado, cai no desenho do bloco estilo Roblox (stdlib pura).

Uso: python tools/make_icon.py [caminho-de-saida.png]
"""
from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

SIZE = 256
SS = 2  # supersampling do fallback

# Gradiente alvo do Blunix
BLUE_A = (10, 132, 255)   # #0A84FF (substitui o verde claro)
BLUE_B = (0, 229, 255)    # #00E5FF (substitui o verde escuro)

# Gradiente original do Sober (SVG: #98E357 → #26A269)
GREEN_A = (152, 227, 87)
GREEN_B = (38, 162, 105)


def _find_sober_icon() -> Path | None:
    """Procura o PNG de 256px (128x128@2) do Sober no flatpak (sistema ou usuário)."""
    patterns = [
        "/var/lib/flatpak/app/org.vinegarhq.Sober/current/active/files/share/app-info/icons/flatpak/128x128@2/*.png",
        str(Path.home() / ".local/share/flatpak/app/org.vinegarhq.Sober/current/active/files/share/app-info/icons/flatpak/128x128@2/*.png"),
        "/var/lib/flatpak/app/org.vinegarhq.Sober/*/active/files/share/app-info/icons/flatpak/128x128@2/*.png",
    ]
    import glob
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return Path(matches[0])
    return None


def _recolor_sober(src: Path, dst: Path) -> None:
    """Carrega o PNG do Sober, troca o gradiente verde pelo azul e salva."""
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf

    pix = GdkPixbuf.Pixbuf.new_from_file(str(src))
    if pix.get_n_channels() < 4:
        pix = pix.add_alpha(False, 0, 0, 0)
    w, h, n, stride = pix.get_width(), pix.get_height(), pix.get_n_channels(), pix.get_rowstride()
    buf = bytearray(pix.get_pixels())

    # direção do gradiente verde (A→B) para projetar cada pixel
    d = tuple(GREEN_B[i] - GREEN_A[i] for i in range(3))
    dd = sum(c * c for c in d) or 1

    for y in range(h):
        row = y * stride
        for x in range(w):
            i = row + x * n
            r, g, b, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
            if a < 10 or (r > 240 and g > 240 and b > 240):
                buf[i + 3] = 0  # fundo branco/transparente -> transparente
                continue
            v = (r - GREEN_A[0], g - GREEN_A[1], b - GREEN_A[2])
            t = sum(v[j] * d[j] for j in range(3)) / dd
            t = max(0.0, min(1.0, t))
            buf[i] = round(BLUE_A[0] + (BLUE_B[0] - BLUE_A[0]) * t)
            buf[i + 1] = round(BLUE_A[1] + (BLUE_B[1] - BLUE_A[1]) * t)
            buf[i + 2] = round(BLUE_A[2] + (BLUE_B[2] - BLUE_A[2]) * t)

    from gi.repository import GLib
    out = GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(bytes(buf)), GdkPixbuf.Colorspace.RGB, True, 8, w, h, stride
    )
    out.savev(str(dst), "png", [], [])
    print(f"ícone (base Sober, recolorido): {dst} ({dst.stat().st_size} bytes, {w}x{h})")


# ---------------------------------------------------------------- fallback (stdlib puro)
BLOCK_ANGLE_DEG = -12.0
BLOCK_HALF = 78
HOLE_HALF = 29
_COS = math.cos(math.radians(BLOCK_ANGLE_DEG))
_SIN = math.sin(math.radians(BLOCK_ANGLE_DEG))


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _sample(x: float, y: float) -> tuple[int, int, int, int]:
    cx = cy = SIZE / 2
    dx, dy = x - cx, y - cy
    rx = dx * _COS - dy * _SIN
    ry = dx * _SIN + dy * _COS
    if abs(rx) <= BLOCK_HALF and abs(ry) <= BLOCK_HALF:
        if abs(rx) <= HOLE_HALF and abs(ry) <= HOLE_HALF:
            return (0, 0, 0, 0)
        t = max(0.0, min(1.0, ((rx + ry) + BLOCK_HALF * 2) / (BLOCK_HALF * 4)))
        return _lerp(BLUE_A, BLUE_B, t) + (255,)
    return (0, 0, 0, 0)


def _draw_block_fallback(dst: Path) -> None:
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)
        for x in range(SIZE):
            ar = ag = ab = aa = 0
            for sy in range(SS):
                for sx in range(SS):
                    c = _sample(x + (sx + 0.5) / SS, y + (sy + 0.5) / SS)
                    ar += c[0]; ag += c[1]; ab += c[2]; aa += c[3]
            n = SS * SS
            raw.extend((ar // n, ag // n, ab // n, aa // n))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    dst.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    )
    print(f"ícone (bloco desenhado): {dst} ({dst.stat().st_size} bytes)")


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/com.github.fernando.blunix.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    sober = _find_sober_icon()
    if sober is not None:
        try:
            _recolor_sober(sober, out)
            return
        except Exception as exc:  # noqa: BLE001
            print(f"aviso: recolor do Sober falhou ({exc}); usando fallback")
    _draw_block_fallback(out)


if __name__ == "__main__":
    main()
