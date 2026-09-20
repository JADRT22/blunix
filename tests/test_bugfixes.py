"""Regressão: bugs encontrados na revisão manual.

- remove_path não deve aceitar traversal nem falso positivo de prefixo
- run_checks usa cache (subprocessos caros não rodam 3x na abertura)
"""
from __future__ import annotations

import pytest

from blunix import environment, mods


def test_remove_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(mods.constants, "SOBER_ASSET_OVERLAY", tmp_path / "overlay")
    root = mods.overlay_root()
    root.mkdir(parents=True)
    secret = tmp_path / "secret.txt"
    secret.write_text("nao apague", encoding="utf-8")
    with pytest.raises(mods.ModError):
        mods.remove_path("../secret.txt")
    assert secret.exists()  # intacto


def test_remove_path_prefix_confusion(tmp_path, monkeypatch):
    """root=/a/b não deve deixar passar alvo em /a/bc (falso positivo de prefixo)."""
    base = tmp_path / "a"
    root = base / "b"
    monkeypatch.setattr(mods.constants, "SOBER_ASSET_OVERLAY", root)
    root.mkdir(parents=True)
    other = base / "bc.txt"
    other.write_text("x", encoding="utf-8")
    with pytest.raises(mods.ModError):
        mods.remove_path("../bc.txt")
    assert other.exists()


def test_run_checks_is_cached(monkeypatch):
    calls = {"n": 0}

    def fake_checks():
        calls["n"] += 1
        return [environment.Check("x", environment.Status.OK, "ok")]

    monkeypatch.setattr(environment, "_run_checks_uncached", fake_checks)
    monkeypatch.setattr(environment, "_CACHE", None)
    a = environment.run_checks()
    b = environment.run_checks()
    assert calls["n"] == 1  # segunda chamada veio do cache
    assert a == b
    environment.run_checks(use_cache=False)
    assert calls["n"] == 2  # force reexecuta
