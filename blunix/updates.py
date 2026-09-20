"""Checagem de atualização via GitHub Releases.

Consulta a API pública do repositório (latest release) e compara com a
versão local. Falha de rede nunca propaga: retorna found=False.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass

from . import constants

REPO = "JADRT22/blunix"
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
    if not is_newer(tag, constants.VERSION):
        return UpdateInfo(current=constants.VERSION, latest=tag.lstrip("v"), url=url, found=False)
    return UpdateInfo(current=constants.VERSION, latest=tag.lstrip("v"), url=url, found=True)
