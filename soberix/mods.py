"""Gerenciador de mods via asset_overlay do Sober.

O overlay espelha a estrutura `assets/` do base.apk do cliente Android
(`packages/*/com.roblox.client/base.apk!assets`), então um mod que substitui
`content/textures/Cursors/KeyboardMouse/ArrowCursor.png` deve viver em
`asset_overlay/content/textures/Cursors/KeyboardMouse/ArrowCursor.png`.

Fonte: https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html
"""
from __future__ import annotations

import logging
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import constants

log = logging.getLogger(__name__)

# Extensões consideradas "assets" de conteúdo (texto, imagens, áudio, modelos)
_ALLOWED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".wav", ".ogg", ".mp3",
    ".mesh", ".fbx", ".obj", ".txt", ".json", ".csv", ".lua",
}

# Caminhos perigosos: sobrescrever isso pode quebrar o cliente
_BLOCKED_PREFIXES = ("scripts/", "fonts/")


class ModError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstalledMod:
    rel_path: str
    size: int


def overlay_root() -> Path:
    return constants.SOBER_ASSET_OVERLAY


def list_mods() -> list[InstalledMod]:
    root = overlay_root()
    if not root.is_dir():
        return []
    mods: list[InstalledMod] = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            mods.append(InstalledMod(rel_path=rel, size=p.stat().st_size))
    return mods


def _validate_zip_member(name: str) -> None:
    """Rejeita paths suspeitos (zip-slip) e caminhos bloqueados."""
    p = Path(name)
    if p.is_absolute() or ".." in p.parts:
        raise ModError(f"Entrada perigosa no zip: {name!r}")
    parts = [part for part in p.parts if part not in ("__MACOSX",)]
    if not parts:
        return  # diretório vazio/entrada utilitária
    rel = Path(*parts).as_posix()
    if rel.startswith(_BLOCKED_PREFIXES):
        raise ModError(f"Entrada bloqueada por segurança: {rel!r}")
    if p.suffix.lower() not in _ALLOWED_SUFFIXES and not p.suffix == "":
        raise ModError(
            f"Extensão não suportada: {name!r}. Permitidas: {', '.join(sorted(_ALLOWED_SUFFIXES))}"
        )


def install_file(rel_path: str, src: Path, *, overwrite: bool = True) -> str:
    """Instala um arquivo único no overlay (usado pelos presets de mods).

    Mesmas validações do zip: extensão permitida, sem path traversal,
    sem prefixos bloqueados. Retorna o caminho relativo instalado.
    """
    rel_path = rel_path.replace("\\", "/").strip("/")
    _validate_zip_member(rel_path)
    if not src.is_file():
        raise ModError(f"Arquivo de origem não encontrado: {src}")
    root = overlay_root()
    dest = root / rel_path
    if dest.exists() and not overwrite:
        raise ModError(f"Destino já existe (use overwrite): {rel_path}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    log.info("Mod instalado: %s", rel_path)
    return rel_path


def install_zip(zip_path: Path, *, overwrite: bool = True) -> list[str]:
    """Instala um mod .zip no asset_overlay, preservando a estrutura de pastas.

    Retorna a lista de caminhos relativos instalados.
    """
    if not zip_path.is_file():
        raise ModError(f"Arquivo não encontrado: {zip_path}")
    root = overlay_root()
    root.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise ModError(f"Zip corrompido (entrada {bad!r})")
        for member in zf.infolist():
            name = member.filename
            if member.is_dir():
                continue
            _validate_zip_member(name)
            parts = [part for part in Path(name).parts if part != "__MACOSX"]
            if not parts:
                continue
            rel = Path(*parts)
            dest = root / rel
            if dest.exists() and not overwrite:
                raise ModError(f"Destino já existe (use --overwrite): {rel}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)
            installed.append(rel.as_posix())
    log.info("Mod instalado: %s (%d arquivos)", zip_path.name, len(installed))
    return installed


def remove_path(rel_path: str) -> bool:
    """Remove um arquivo (ou pasta inteira) do overlay. Retorna True se removeu."""
    root = overlay_root().resolve()
    target = (root / rel_path).resolve()
    # is_relative_to evita falso positivo de prefixo (ex.: root '/foo/bar' vs '/foo/barbaz')
    if not target.is_relative_to(root):
        raise ModError("Caminho fora do asset_overlay")
    if target.is_dir():
        shutil.rmtree(target)
        log.info("Pasta de mod removida: %s", rel_path)
        return True
    if target.is_file():
        target.unlink()
        log.info("Mod removido: %s", rel_path)
        # limpa pastas vazias pai a pai
        parent = target.parent
        while parent != root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
        return True
    return False


def clear_all() -> int:
    """Remove todos os mods. Retorna quantos arquivos foram removidos."""
    root = overlay_root()
    if not root.is_dir():
        return 0
    count = sum(1 for p in root.rglob("*") if p.is_file())
    shutil.rmtree(root)
    log.info("asset_overlay limpo (%d arquivos)", count)
    return count
