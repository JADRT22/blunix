"""Checagem de atualização via GitHub Releases.

Consulta a API pública do repositório (latest release) e compara com a
versão local. Falha de rede nunca propaga: retorna found=False.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import constants

REPO = "JADRT22/soberix"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
TIMEOUT = 5  # segundos — UI não pode travar

# aceita 2 ou 3 componentes (1.0, 1.2.3…)
_V_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    url: str
    found: bool
    # URLs de download dos assets (AppImage etc.) da release mais recente
    download_urls: tuple[str, ...] = ()


def _parse(v: str) -> tuple[int, int, int] | None:
    m = _V_RE.search(v or "")
    if not m:
        return None
    return (int(m[1]), int(m[2]), int(m[3] or 0))


def is_newer(latest: str, current: str) -> bool:
    a, b = _parse(latest), _parse(current)
    if not a or not b:
        return False
    return a > b


def check() -> UpdateInfo:
    """Verifica a última release; qualquer problema -> found=False."""
    info = UpdateInfo(current=constants.VERSION, latest="", url="", found=False)
    try:
        req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):  # urllib.HTTPError é subclass de OSError
        return info
    tag = data.get("tag_name") or ""
    url = data.get("html_url") or f"https://github.com/{REPO}/releases/latest"
    downloads = tuple(
        a["browser_download_url"]
        for a in data.get("assets") or []
        if isinstance(a, dict) and a.get("name", "").endswith(".AppImage")
    )
    if not is_newer(tag, constants.VERSION):
        return UpdateInfo(current=constants.VERSION, latest=tag.lstrip("v"), url=url,
                          found=False, download_urls=downloads)
    return UpdateInfo(current=constants.VERSION, latest=tag.lstrip("v"), url=url,
                      found=True, download_urls=downloads)


def download_asset(url: str, timeout: float = 60.0) -> tuple[bool, str]:
    """Baixa um asset (AppImage) para ~/Downloads, pronto para executar.

    Escrita atômica (.part -> rename) e chmod +x. Retorna (ok, caminho).
    """
    if not url.startswith("http"):
        return False, ""
    dest = Path.home() / "Downloads" / url.rsplit("/", 1)[-1]
    if not dest.name:
        return False, ""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": "soberix/1.5"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as f:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        tmp.replace(dest)
        os.chmod(dest, 0o755)
        return True, str(dest)
    except (OSError, ValueError):
        try:
            tmp.unlink(missing_ok=True)
        except (OSError, NameError, UnboundLocalError):
            pass
        return False, ""
