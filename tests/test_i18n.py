"""Testes do i18n (pt/en)."""
from __future__ import annotations

import pytest

from blunix import i18n, settings


@pytest.fixture(autouse=True)
def reset_lang_cache():
    """Cada teste começa com o cache de idioma limpo."""
    i18n._LANG = None
    yield
    i18n._LANG = None


def test_default_is_auto_and_en_by_env(monkeypatch):
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    monkeypatch.delenv("LANGUAGE", raising=False)
    assert i18n.lang() == "en"
    assert i18n.t("menu.play") == "🎮  PLAY"


def test_auto_pt(monkeypatch):
    monkeypatch.setenv("LC_ALL", "pt_BR.UTF-8")
    assert i18n.lang() == "pt"
    assert i18n.t("menu.play") == "🎮  JOGAR"


def test_saved_language_wins(monkeypatch):
    settings.save({"language": "en"})
    monkeypatch.setenv("LC_ALL", "pt_BR.UTF-8")  # ambiente pt, mas salvo en
    assert i18n.lang() == "en"


def test_fallback_to_pt_for_unknown_key():
    assert i18n.t("chave.inexistente") == "chave.inexistente"


def test_all_keys_present_in_both_languages():
    """Toda chave de pt deve existir em en (e vice-versa)."""
    assert set(i18n.STRINGS["pt"]) == set(i18n.STRINGS["en"])


def test_format_args():
    i18n._LANG = "en"
    assert i18n.t("chk.sober.ok", ver="1.2.3") == "installed (version 1.2.3)"
    assert i18n.t("menu.falta", items="Sober") == "⚠ Missing: Sober"
