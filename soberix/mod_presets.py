"""Presets de mods populares — 1 clique para instalar no asset_overlay.

- "Mute death sound": embutido no próprio Soberix (ver mod_assets.py) —
  funciona offline, sem fonte externa.
- Sons antigos (2006/2013) e cursores clássicos: as URLs originais morreram
  com o arquivamento do bloxstrap-resources; os presets permanecem
  catalogados e voltam a funcionar assim que `MIRROR_BASE` apontar para um
  espelho da comunidade (basta editar UMA constante).

Caminhos relativos seguem a estrutura do base.apk (VinegarHQ TipsAndTricks):
content/sounds/uuhhh.mp3, content/textures/Cursors/KeyboardMouse/...
"""
from __future__ import annotations

import base64
import tempfile
import urllib.request
from pathlib import Path

from . import mods

# Troque quando houver espelho vivo dos assets clássicos (None = indisponível)
MIRROR_BASE: str | None = None

_EMBEDDED = {
    "content/sounds/uuhhh.mp3": lambda: _mute_mp3(),
}

# (id, nome de exibição, descrição curta, ((caminho no overlay, url-path), ...))
MOD_PRESETS: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        "mute-death-sound",
        "Mute death sound",
        "Silences the death sound — embedded, works offline.",
        (("content/sounds/uuhhh.mp3", "embedded:mute-death"),),
    ),
    (
        "death-sound-2006",
        "Old 2006 death sound",
        "The classic 'uuhhh' death sound.",
        (("content/sounds/uuhhh.mp3", "sounds/old/uuhhh.mp3"),),
    ),
    (
        "death-sound-2013",
        "2013 death sound",
        "The 2013 'aaaah' death sound.",
        (("content/sounds/ouch.mp3", "sounds/ouch.mp3"),),
    ),
    (
        "cursor-2006",
        "Classic 2006 cursors",
        "The original arrow/beam cursor set.",
        (
            ("content/textures/Cursors/KeyboardMouse/ArrowCursor.png", "cursors/2006/ArrowCursor.png"),
            ("content/textures/Cursors/KeyboardMouse/ArrowFarCursor.png", "cursors/2006/ArrowFarCursor.png"),
            ("content/textures/Cursors/KeyboardMouse/IBeamCursor.png", "cursors/2006/IBeamCursor.png"),
        ),
    ),
)


class PresetError(ValueError):
    pass


def get_preset(name: str) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    for pid, display, desc, files in MOD_PRESETS:
        if pid == name:
            return pid, display, files
    raise PresetError(
        f"Preset desconhecido: {name!r}. Disponíveis: {', '.join(p[0] for p in MOD_PRESETS)}"
    )


def preset_available(name: str) -> bool:
    """True se o preset pode ser instalado agora (embutido ou espelho ativo).

    Presets dormientes (sem espelho de assets) devem aparecer desabilitados
    na GUI/CLI em vez de falhar com erro de rede ao clicar.
    """
    if MIRROR_BASE:
        return True
    _pid, _display, files = get_preset(name)
    return any(spec.startswith("embedded:") for _p, spec in files)


def _mute_mp3() -> bytes:
    from .mod_assets import muted_death_sound

    return muted_death_sound()


def _download(url: str, dest: Path, timeout: float = 30.0) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "soberix/1.6"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(128 * 1024)
            if not chunk:
                break
            f.write(chunk)


def _fetch(rel_or_spec: str, tmp: Path) -> None:
    """Obtém o arquivo: embutido ('embedded:…') ou baixa do espelho."""
    if rel_or_spec.startswith("embedded:"):
        data = _mute_mp3()
        tmp.write_bytes(data)
        return
    if not MIRROR_BASE:
        raise mods.ModError("sem espelho de assets configurado (MIRROR_BASE)")
    _download(f"{MIRROR_BASE}/{rel_or_spec}", tmp)


def install_preset(name: str) -> tuple[list[str], list[str]]:
    """Instala todos os arquivos do preset. Retorna (instalados, falhas)."""
    _pid, _display, files = get_preset(name)
    installed: list[str] = []
    failed: list[str] = []
    for rel_path, spec in files:
        tmp = Path(tempfile.mkstemp(prefix="soberix-mod-", suffix=".part")[1])
        try:
            _fetch(spec, tmp)
            mods.install_file(rel_path, tmp)
            installed.append(rel_path)
        except (mods.ModError, OSError, ValueError):
            failed.append(rel_path)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    return installed, failed
