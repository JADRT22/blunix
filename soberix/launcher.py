"""Lançador do Roblox via Sober.

O Sober aceita deep links (schemes `roblox://` e `roblox-player://`, ver
MimeType do .desktop oficial). Usamos `roblox://experiences/start?placeId=N`
para abrir experiências diretamente.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from . import constants

log = logging.getLogger(__name__)


class LaunchError(RuntimeError):
    pass


def extract_place_id(text: str | None) -> str | None:
    """Extrai um placeId de várias formas de input amigáveis:

    - "12345" (número puro)
    - "roblox://experiences/start?placeId=12345"
    - "roblox-player:1+launchmode:gameplace+placeid:12345+..."
    - "https://www.roblox.com/games/123456/Nome-do-Jogo"

    Retorna None se nada for encontrado (ou lança LaunchError para lixo claro).
    """
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    if text.isdigit():
        return text
    low = text.lower()
    if low.startswith("roblox-player:"):
        # formato do deep link oficial: chunks separados por '+' com 'chave:valor'
        for chunk in text.split("+"):
            key, _, value = chunk.partition(":")
            if key.strip().lower() == "placeid" and value.strip().isdigit():
                return value.strip()
        raise LaunchError("Link roblox-player:// sem placeid válido")
    if "placeid=" in low:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(text)
        qs = parse_qs(parsed.query)
        for v in qs.get("placeId", qs.get("placeid", [])):
            if v.isdigit():
                return v
        raise LaunchError("URL com placeId inválido")
    # URL do site: roblox.com/games/<id>/...
    import re
    m = re.search(r"/games/(\d+)", text)
    if m:
        return m.group(1)
    raise LaunchError(
        f"Não entendi {text!r}. Use um número de placeId, um link roblox:// "
        "ou uma URL roblox.com/games/..."
    )


def build_command(place_id: str | None = None) -> list[str]:
    """Monta o comando flatpak para abrir o Sober (com deep link opcional)."""
    cmd = ["flatpak", "run", constants.FLATPAK_APP_ID]
    if place_id:
        place_id = str(place_id).strip()
        if not place_id.isdigit():
            raise LaunchError(f"placeId inválido: {place_id!r} (deve ser numérico)")
        url = f"roblox://experiences/start?placeId={place_id}"
        cmd.append(url)
    return cmd


def launch(place_id: str | None = None, *, wait: bool = False) -> subprocess.Popen | int:
    """Abre o Roblox (Sober). Aceita número, link roblox:// ou URL do site."""
    place_id = extract_place_id(place_id)
    cmd = build_command(place_id)
    log.info("Lançando: %s", " ".join(cmd))
    if wait:
        return subprocess.run(cmd, check=False).returncode
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_running() -> bool:
    """Verifica se existe processo 'sober' rodando."""
    try:
        out = subprocess.run(
            ["pgrep", "-af", "sober"],
            capture_output=True, text=True, timeout=5, check=False,
        ).stdout
    except OSError:
        return False
    # evita falso-positivo com o próprio pgrep/soberix
    return any(
        line for line in out.splitlines()
        if "soberix" not in line and "pgrep" not in line and "sober" in line
    )
