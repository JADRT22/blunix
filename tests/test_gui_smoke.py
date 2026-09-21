"""Smoke test da GUI: valida a construção real da janela GTK.

Teria pego a regressão v1.5.1 (UnboundLocalError ao montar o menu, que só
explodia em runtime — sintaxe e unitários passavam).

Estratégia: quando gi/GTK4 está disponível (CI instala; venv local não
precisa), constrói a SoberixWindow real com Gtk.init e depois destrói.
Sem GTK, pula — os unitários normais continuam valendo.
"""
from __future__ import annotations

import pytest

gi = pytest.importorskip("gi", reason="PyGObject/GTK4 não disponível")

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402


@pytest.fixture()
def gtk_app():
    # GTK4 exige init explícito antes de criar qualquer widget — sem isso
    # a construção da janela falha no CI (xvfb). No PyGObject, Gtk.init()
    # retorna None (não bool): valide com Gtk.is_initialized().
    if not Gtk.is_initialized():
        Gtk.init()
        assert Gtk.is_initialized(), "GTK não inicializou (display indisponível?)"
    app = Gtk.Application(application_id="com.github.fernando.soberix.test")
    app.register(None)
    yield app
    for win in app.get_windows():
        win.destroy()


def test_menu_page_builds_and_activity_row_renders(gtk_app):
    """O menu inteiro é construído sem exceção — inclui o card de atividade."""
    from soberix.gui import SoberixWindow

    win = SoberixWindow(application=gtk_app)
    try:
        assert win.get_child() is not None  # menu montado
        # o card de atividade existe e tem conteúdo (ou está vazio legítimo)
        assert hasattr(win, "activity_row")
        assert hasattr(win, "servers_list") or not hasattr(win, "inner_stack")
    finally:
        watcher = getattr(win, "_activity_watcher", None)
        if watcher is not None:
            watcher.stop()
        win.destroy()


def test_selected_profile_returns_preset_id(gtk_app):
    """regressão v1.4: o dropdown devolve id de preset, não chave de tradução."""
    from soberix.gui import SoberixWindow

    win = SoberixWindow(application=gtk_app)
    try:
        assert win._selected_profile() in {"leve", "medio", "completo", "default"}
    finally:
        watcher = getattr(win, "_activity_watcher", None)
        if watcher is not None:
            watcher.stop()
        win.destroy()


def test_resolve_name_async_has_no_unbound_local(gtk_app):
    """regressão v1.5.1: chamar o resolver com cache vazio não explode."""
    from soberix.gui import SoberixWindow

    win = SoberixWindow(application=gtk_app)
    try:
        win._resolved_names = set()  # cache pré-existente: pega o caminho do bug
        win._resolve_name_async("1")  # não deve levantar UnboundLocalError
    finally:
        watcher = getattr(win, "_activity_watcher", None)
        if watcher is not None:
            watcher.stop()
        win.destroy()
