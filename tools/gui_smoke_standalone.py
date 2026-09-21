"""Verificação standalone do smoke test (sem pytest) — roda com o python do sistema.

Reproduz o caminho do CI: Gtk.init() explícito -> construção da janela real.
Uso: python3 tools/gui_smoke_standalone.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

if not Gtk.is_initialized():
    Gtk.init()
    assert Gtk.is_initialized(), "GTK não inicializou (display indisponível?)"

app = Gtk.Application(application_id="com.github.fernando.soberix.smoke")
app.register(None)

from soberix.gui import SoberixWindow  # noqa: E402

win = SoberixWindow(application=app)
try:
    assert win.get_child() is not None, "menu não montado"
    assert hasattr(win, "activity_row"), "card de atividade ausente"
    assert win._selected_profile() in {"leve", "medio", "completo", "default"}, (
        f"perfil devolve id errado: {win._selected_profile()!r}"
    )
    win._resolved_names = set()
    win._resolve_name_async("1")  # regressão v1.5.1: UnboundLocalError
    print("SMOKE OK: janela construída, perfil ok, resolver ok")
finally:
    watcher = getattr(win, "_activity_watcher", None)
    if watcher is not None:
        watcher.stop()
    win.destroy()
