"""Integração com o desktop: instalar/remover atalho no menu de aplicativos.

Instala um .desktop no usuário (~/.local/share/applications) que aponta para
o AppImage ou para o diretório do código, com ícone e nome amigáveis.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import constants

APPS_DIR = Path.home() / ".local/share/applications"
HICOLOR_BASE = Path.home() / ".local/share/icons/hicolor"
ICONS_DIR = HICOLOR_BASE / "256x256/apps"
ICON_SIZES = (48, 64, 128, 256)  # tamanhos padrão que o KDE/GNOME consultam
DESKTOP_ID = "com.github.fernando.blunix"

# Cores do gradiente: Sober (verde) -> Blunix (azul)
_SVG_RECOLOR = (("#98E357", "#0A84FF"), ("#26A269", "#00E5FF"))


def find_sober_svg() -> Path | None:
    for c in (
        Path("/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps/org.vinegarhq.Sober.svg"),
        Path.home() / ".local/share/flatpak/exports/share/icons/hicolor/scalable/apps/org.vinegarhq.Sober.svg",
    ):
        if c.is_file():
            return c
    return None


def recolor_sober_svg(dest: Path) -> Path | None:
    """Copia o SVG do Sober trocando o gradiente verde pelo azul do Blunix."""
    src = find_sober_svg()
    if src is None:
        return None
    try:
        text = src.read_text(encoding="utf-8")
        for old, new in _SVG_RECOLOR:
            text = text.replace(old, new)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        return dest
    except OSError:
        return None


def install_icon_files(master_png: Path) -> list[Path]:
    """Instala o ícone no tema hicolor em vários tamanhos + SVG vetorial.

    A taskbar do KDE consulta 48/64/128/256 e o cache ksycoca; instalar só o
    256px faz o ícone aparecer quebrado/corrompido em alguns temas.
    """
    installed: list[Path] = []
    # 1) master 256
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    m = ICONS_DIR / f"{DESKTOP_ID}.png"
    shutil.copy2(master_png, m)
    installed.append(m)
    # 2) tamanhos menores (downscale via GdkPixbuf; se indisponível, pula)
    try:
        import gi

        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf

        for size in ICON_SIZES[:-1]:
            d = HICOLOR_BASE / f"{size}x{size}/apps"
            d.mkdir(parents=True, exist_ok=True)
            dest = d / f"{DESKTOP_ID}.png"
            pix = GdkPixbuf.Pixbuf.new_from_file_at_size(str(master_png), size, size)
            pix.savev(str(dest), "png", [], [])
            installed.append(dest)
    except Exception:  # noqa: BLE001 - GdkPixbuf indisponível: segue só com 256px
        pass
    # 3) SVG vetorial (base Sober recolorida) — nítido em qualquer tamanho
    svg = recolor_sober_svg(HICOLOR_BASE / "scalable/apps" / f"{DESKTOP_ID}.svg")
    if svg is not None:
        installed.append(svg)
    return installed


class MenuError(RuntimeError):
    pass


@dataclass(frozen=True)
class MenuInstallResult:
    desktop_path: Path
    icon_path: Path | None
    exec_line: str


def find_icon() -> Path | None:
    """Procura o ícone no projeto (instalação por código) ou junto ao executável (AppImage)."""
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / f"{DESKTOP_ID}.png",
        Path(__file__).resolve().parent / "share" / f"{DESKTOP_ID}.png",
    ]
    # dentro de AppImage extraído: blunix/ fica em usr/lib/blunix/
    appimage = os.environ.get("APPDIR")
    if appimage:
        candidates.append(Path(appimage) / "usr/share/icons/hicolor/256x256/apps" / f"{DESKTOP_ID}.png")
    for c in candidates:
        if c.is_file():
            return c
    return None


def _exec_line() -> str:
    """Como o menu deve abrir o Blunix (AppImage > venv > python -m)."""
    appimage = os.environ.get("APPIMAGE")
    if appimage and Path(appimage).is_file():
        return appimage
    project_run = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
    if project_run.is_file():
        return f"{project_run} -m blunix"
    if shutil.which("blunix"):
        return "blunix gui"
    return f"{shutil.which('python3') or 'python3'} -m blunix"


def install_menu() -> MenuInstallResult:
    apps_dir = APPS_DIR
    apps_dir.mkdir(parents=True, exist_ok=True)

    exec_line = _exec_line()
    icon_path = find_icon()

    # Instala no tema hicolor (vários tamanhos + SVG) e referencia pelo
    # CAMINHO ABSOLUTO do 256px (estável no HOME): a taskbar do KDE ignora
    # caches de tema quando Icon= é caminho — à prova de ksycoca velho.
    # (o nome no tema continua instalado para menus/busca do sistema)
    installed_icon: Path | None = None
    icon_field = "applications-games"
    if icon_path is not None:
        installed = install_icon_files(icon_path)
        if installed:
            installed_icon = installed[0]
            icon_field = str(installed_icon)
        else:
            icon_field = str(icon_path)

    desktop = f"""[Desktop Entry]
Type=Application
Name=Blunix
GenericName=Roblox for Linux
Comment=Open Roblox (Sober) with one click — configs, flags and mods
Exec={exec_line}
Icon={icon_field}
Categories=Game;Utility;
Keywords=roblox;sober;launcher;play;bloxstrap;
Terminal=false
StartupWMClass=Blunix
"""
    target = apps_dir / f"{DESKTOP_ID}.desktop"
    try:
        unchanged = target.is_file() and target.read_text(encoding="utf-8") == desktop
    except OSError:
        unchanged = False
    if not unchanged:
        target.write_text(desktop, encoding="utf-8")
        os.chmod(target, 0o755)
        # caches só precisam saber quando o conteúdo muda (kbuildsycoca é caro)
        _refresh_db()
    return MenuInstallResult(desktop_path=target, icon_path=installed_icon, exec_line=exec_line)


def uninstall_menu() -> bool:
    target = APPS_DIR / f"{DESKTOP_ID}.desktop"
    removed = False
    candidates = [target]
    for size in (*ICON_SIZES,):
        candidates.append(HICOLOR_BASE / f"{size}x{size}/apps" / f"{DESKTOP_ID}.png")
    candidates.append(HICOLOR_BASE / "scalable/apps" / f"{DESKTOP_ID}.svg")
    for p in candidates:
        if p.exists():
            p.unlink()
            removed = True
    _refresh_db()
    return removed


def is_menu_installed() -> bool:
    return (APPS_DIR / f"{DESKTOP_ID}.desktop").exists()


def _refresh_db() -> None:
    """Atualiza caches de desktop/ícones (best-effort) para o taskbar/dock
    encontrar o ícone imediatamente (KDE precisa do kbuildsycoca)."""
    cmds = [
        ["update-desktop-database", str(APPS_DIR)],
        ["gtk-update-icon-cache", "-f", "-t",
         str(Path.home() / ".local/share/icons/hicolor")],
        ["kbuildsycoca6"], ["kbuildsycoca5"],
    ]
    # ksycoca incremental às vezes não pega ícone novo: força rebuild total
    cmds.insert(0, ["kbuildsycoca6", "--noincremental"])
    for cmd in cmds:
        try:
            subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        except (OSError, subprocess.SubprocessError):
            continue


def self_appimage_path() -> Path | None:
    """Se rodando dentro de um AppImage, retorna o caminho do AppImage."""
    v = os.environ.get("APPIMAGE")
    return Path(v) if v and Path(v).is_file() else None
