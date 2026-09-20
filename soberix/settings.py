"""Preferências simples do Soberix (ex.: perfil de qualidade escolhido).

Fica em ~/.local/state/soberix/settings.json — nada sensível.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import constants

_DEFAULTS = {"profile": "medio", "language": "auto"}


def _path() -> Path:
    constants.SOBERIX_STATE_DIR.mkdir(parents=True, exist_ok=True)
    return constants.SOBERIX_STATE_DIR / "settings.json"


def load() -> dict:
    p = _path()
    data = dict(_DEFAULTS)
    if p.is_file():
        try:
            data.update(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save(updates: dict) -> None:
    data = load()
    data.update(updates)
    tmp = _path().with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_path())
