"""Histórico de jogos (recentes) e favoritos do Blunix.

Fica em ~/.local/state/blunix/games.json — só place IDs e apelidos,
nada sensível. Estrutura:
{
  "recent": [{"id": "2753915549", "name": "Brookhaven RP", "ts": 1690000000}],
  "favorites": ["2753915549"]
}
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from . import constants

MAX_RECENT = 12


@dataclass(frozen=True)
class GameEntry:
    id: str
    name: str
    ts: int = 0


def _path():
    return constants.BLUNIX_STATE_DIR / "games.json"


def _load() -> dict:
    p = _path()
    if not p.is_file():
        return {"recent": [], "favorites": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"recent": [], "favorites": []}
    data.setdefault("recent", [])
    data.setdefault("favorites", [])
    return data


def _save(data: dict) -> None:
    constants.BLUNIX_STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _path().with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_path())


def _normalize(entry: GameEntry | str) -> GameEntry:
    if isinstance(entry, GameEntry):
        return entry
    return GameEntry(id=str(entry), name=str(entry))


def add_recent(place_id: str, name: str | None = None) -> None:
    """Registra/Move um jogo para o topo dos recentes (mantém apelido conhecido)."""
    place_id = str(place_id).strip()
    if not place_id:
        return
    data = _load()
    known = {e["id"]: e for e in data["recent"]}
    name = name or (known.get(place_id, {}).get("name") or place_id)
    entry = {"id": place_id, "name": name, "ts": int(time.time())}
    data["recent"] = [entry] + [e for e in data["recent"] if e["id"] != place_id]
    data["recent"] = data["recent"][:MAX_RECENT]
    _save(data)


def recent() -> list[GameEntry]:
    return [GameEntry(id=e["id"], name=e.get("name") or e["id"], ts=e.get("ts", 0))
            for e in _load()["recent"]]


def favorites() -> list[str]:
    return list(_load()["favorites"])


def is_favorite(place_id: str) -> bool:
    return str(place_id) in _load()["favorites"]


def toggle_favorite(place_id: str, name: str | None = None) -> bool:
    """Alterna favorito; retorna o novo estado."""
    place_id = str(place_id).strip()
    data = _load()
    favs = [p for p in data["favorites"] if p != place_id]
    now_fav = len(favs) == len(data["favorites"])
    if now_fav:
        favs.insert(0, place_id)
        # garante que favorito também apareça nos recentes
        add_recent(place_id, name)
        data = _load()
    data["favorites"] = favs
    _save(data)
    return now_fav


def remove(place_id: str) -> None:
    data = _load()
    data["recent"] = [e for e in data["recent"] if e["id"] != str(place_id)]
    data["favorites"] = [p for p in data["favorites"] if p != str(place_id)]
    _save(data)


def clear() -> None:
    _save({"recent": [], "favorites": []})
