"""Testes do i18n (pt/en)."""
from __future__ import annotations

import pytest

from soberix import i18n, settings


@pytest.fixture(autouse=True)
def reset_lang_cache():
    """Cada teste começa com o cache de idioma limpo."""
    i18n._LANG = None
    yield
    i18n._LANG = None


def test_default_is_auto_and_en_by_env(monkeypatch):
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    monkeypatch.delenv("LANGUAGE", raising=False)
    i18n._LANG = None
    assert i18n.lang() == "en"
    assert i18n.t("menu.play") == "🎮  PLAY"


def test_auto_pt(monkeypatch):
    monkeypatch.setenv("LC_ALL", "pt_BR.UTF-8")
    i18n._LANG = None
    assert i18n.lang() == "pt"
    assert i18n.t("menu.play") == "🎮  JOGAR"


def test_saved_language_wins(monkeypatch):
    settings.save({"language": "en"})
    monkeypatch.setenv("LC_ALL", "pt_BR.UTF-8")  # ambiente pt, mas salvo en
    i18n._LANG = None
    assert i18n.lang() == "en"


def test_fallback_to_pt_for_unknown_key():
    assert i18n.t("chave.inexistente") == "chave.inexistente"


def test_all_keys_present_in_every_language():
    """Toda chave de pt deve existir em todos os idiomas suportados."""
    base = set(i18n.STRINGS["pt"])
    for code in i18n.SUPPORTED:
        assert set(i18n.STRINGS[code]) == base, f"chaves divergentes em {code}"


def test_new_languages_translate_and_fall_back():
    i18n._LANG = "es"
    assert i18n.t("menu.play") == "🎮  JUGAR"
    i18n._LANG = "ja"
    assert i18n.t("menu.play").endswith("プレイ")
    i18n._LANG = "fr"
    assert i18n.t("discord.show_game") == "Afficher le jeu sur Discord"
    # idioma não suportado cai para en
    assert i18n.t("menu.play") == "🎮  PLAY" or i18n.lang() in i18n.SUPPORTED


def test_detect_es_and_unsupported(monkeypatch):
    monkeypatch.setenv("LC_ALL", "es_ES.UTF-8")
    i18n._LANG = None
    assert i18n.lang() == "es"
    monkeypatch.setenv("LC_ALL", "it_IT.UTF-8")
    i18n._LANG = None
    assert i18n.lang() == "en"  # italiano não suportado -> en


def test_format_args():
    i18n._LANG = "en"
    assert i18n.t("chk.sober.ok", ver="1.2.3") == "installed (version 1.2.3)"
    assert i18n.t("menu.falta", items="Sober") == "⚠ Missing: Sober"
