"""Testes de history (recentes/favoritos) e updates (checagem de release)."""
from __future__ import annotations

import urllib.error

from blunix import history, updates


# ---------------------------------------------------------------- history
def test_add_recent_and_dedupe():
    history.clear()
    history.add_recent("111", "Alpha")
    history.add_recent("222", "Beta")
    history.add_recent("111")  # de novo: sobe para o topo, mantém nome
    entries = history.recent()
    assert [e.id for e in entries] == ["111", "222"]
    assert entries[0].name == "Alpha"


def test_recent_limit():
    history.clear()
    for i in range(20):
        history.add_recent(str(i), f"game{i}")
    assert len(history.recent()) == history.MAX_RECENT


def test_toggle_favorite_on_off():
    history.clear()
    assert history.toggle_favorite("42", "Answer") is True
    assert history.is_favorite("42")
    # favorito também entra nos recentes
    assert any(e.id == "42" for e in history.recent())
    assert history.toggle_favorite("42") is False
    assert not history.is_favorite("42")


def test_add_recent_resolve_updates_name(monkeypatch):
    """resolve=True busca o nome oficial e atualiza a entrada (best effort)."""
    history.clear()

    class R:
        def __init__(self, payload):
            self._p = payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self._p

    payloads = iter([
        b'{"universeId": 99}',                              # universes API
        b'{"data": [{"name": "Brookhaven RP"}]}',          # games API
    ])
    monkeypatch.setattr(updates.urllib.request, "urlopen",
                        lambda *a, **k: R(next(payloads)))
    # o módulo history tem seu próprio urllib: patchea também
    monkeypatch.setattr(history.urllib.request, "urlopen",
                        lambda *a, **k: R(next(payloads, b"{}")))

    done = []
    history.add_recent("2753915549", resolve=True, on_name=done.append)
    # espera a thread resolver (timeout generoso)
    import time as _t
    for _ in range(50):
        _t.sleep(0.05)
        if done:
            break
    assert done and done[0] == "Brookhaven RP"
    assert history.recent()[0].name == "Brookhaven RP"


def test_remove_and_clear():
    history.clear()
    history.add_recent("1", "One")
    history.add_recent("2", "Two")
    history.toggle_favorite("1")
    history.remove("2")
    assert [e.id for e in history.recent()] == ["1"]
    history.clear()
    assert history.recent() == [] and history.favorites() == []


# ---------------------------------------------------------------- updates
def test_is_newer():
    assert updates.is_newer("v0.3.0", "0.2.1")
    assert updates.is_newer("0.2.10", "0.2.9")
    assert not updates.is_newer("v0.2.1", "0.2.1")
    assert not updates.is_newer("0.2.0", "0.2.1")
    assert not updates.is_newer("garbage", "0.2.1")


def test_check_newer(monkeypatch):
    class R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"tag_name": "v9.9", "html_url": "https://example.com/rel"}'

    monkeypatch.setattr(updates.urllib.request, "urlopen", lambda *a, **k: R())
    info = updates.check()
    assert info.found and info.latest == "9.9" and info.url == "https://example.com/rel"


def test_check_same_version(monkeypatch):
    class R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"tag_name": "v1.0"}'

    monkeypatch.setattr(updates.urllib.request, "urlopen", lambda *a, **k: R())
    info = updates.check()
    assert not info.found


def test_check_offline(monkeypatch):
    def boom(*a, **k):
        raise urllib.error.URLError("no net")

    monkeypatch.setattr(updates.urllib.request, "urlopen", boom)
    info = updates.check()
    assert not info.found and info.latest == ""
