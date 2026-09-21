"""Re-registro automático do atalho do menu após um update.

O problema: a GUI re-instala o atalho a cada abertura, mas sempre apontando
para o AppImage **em execução** — se o usuário baixa um novo AppImage e abre
o novo binário diretamente (sem apagar o antigo), o atalho continua lançando
o binário velho para sempre.

A solução: na abertura da GUI, se estamos rodando de dentro de um AppImage,
procuramos AppImages do Soberix nos diretórios de download padrão e, se algum
tiver versão **maior** que a do atalho atual, o atalho é reescrito para o
mais novo (o usuário é avisado pela GUI).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import desktop_integration
from .updates import _parse as _parse_version

# Diretórios onde navegadores salvam downloads por padrão (pt-BR usa "Downloads";
# entradas extras cobrem localidades com nomes traduzidos de pasta de downloads)
DOWNLOAD_DIRS = (
    Path.home() / "Downloads",
    Path.home() / "Descargas",        # es
    Path.home() / "Téléchargements",  # fr
)

_NAME_RE = re.compile(r"^Soberix-(\d+(?:\.\d+)*(-\w+)?)-x86_64\.AppImage$", re.IGNORECASE)


@dataclass(frozen=True)
class ShortcutUpdate:
    old_exec: str
    new_exec: str
    new_version: str


def _appimage_version(path: Path) -> tuple[int, int, int] | None:
    """Extrai a versão do nome de um AppImage do Soberix (None se não casar)."""
    m = _NAME_RE.match(path.name)
    if not m:
        return None
    return _parse_version(m.group(1))


def _shortcut_version(desktop_path: Path) -> tuple[int, int, int] | None:
    """Versão do AppImage apontado pelo Exec= do atalho atual (None se impossível)."""
    try:
        for line in desktop_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Exec="):
                return _appimage_version(Path(line[5:].strip()))
    except OSError:
        return None
    return None


def _shortcut_exec(desktop_path: Path) -> str | None:
    """Linha Exec= atual do atalho (None se o arquivo não existir/ilegível)."""
    try:
        for line in desktop_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Exec="):
                return line[5:].strip()
    except OSError:
        return None
    return None


def find_newer_appimage(*, current: tuple[int, int, int] | None = None) -> Path | None:
    """Procura o AppImage mais novo nos diretórios de download.

    `current` é a versão mínima exigida (por padrão, a do atalho instalado).
    Retorna o caminho do binário mais novo encontrado, ou None.
    """
    if current is None:
        current = _shortcut_version(
            desktop_integration.APPS_DIR / f"{desktop_integration.DESKTOP_ID}.desktop"
        )
    if current is None:
        return None
    best: Path | None = None
    best_v = current
    for d in DOWNLOAD_DIRS:
        try:
            candidates = list(d.glob("Soberix-*.AppImage"))
        except OSError:
            continue
        for p in candidates:
            v = _appimage_version(p)
            if v is None or not p.is_file():
                continue
            if v > best_v:
                best, best_v = p, v
    return best


def refresh_shortcut() -> ShortcutUpdate | None:
    """Se houver AppImage mais novo que o do atalho, reaponta o atalho.

    Só age quando o próprio Soberix roda de dentro de um AppImage (o atalho
    de quem roda do código aponta para o python do projeto, não para binário).
    Retorna o que mudou, ou None se nada a fazer.
    """
    appimage = os.environ.get("APPIMAGE")
    if not appimage or not Path(appimage).is_file():
        return None
    desktop_path = desktop_integration.APPS_DIR / f"{desktop_integration.DESKTOP_ID}.desktop"
    old_exec = _shortcut_exec(desktop_path) or ""
    newer = find_newer_appimage()
    if newer is None:
        return None
    # Reinstala o atalho com APPIMAGE apontando para o binário mais novo:
    # _exec_line() prioriza o env APPIMAGE, então o definimos antes de instalar.
    os.environ["APPIMAGE"] = str(newer)
    try:
        desktop_integration.install_menu()
    finally:
        os.environ["APPIMAGE"] = appimage  # restaura o processo atual
    v = _appimage_version(newer)
    return ShortcutUpdate(old_exec=old_exec, new_exec=str(newer),
                          new_version=".".join(map(str, v)) if v else "")
