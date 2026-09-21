"""Re-registro automático do atalho quando há AppImage mais novo nos downloads."""
from __future__ import annotations

from pathlib import Path

import pytest

from soberix import desktop_integration, shortcut_refresh


def _make_appimage(directory: Path, version: str) -> Path:
    p = directory / f"Soberix-{version}-x86_64.AppImage"
    p.write_bytes(b"fake")  # só precisa existir
    return p


# ---------------------------------------------------------------- parsing
def test_appimage_version_from_name():
    assert shortcut_refresh._appimage_version(Path("Soberix-1.4.1-x86_64.AppImage")) == (1, 4, 1)
    assert shortcut_refresh._appimage_version(Path("soberix-1.2-x86_64.appimage")) == (1, 2, 0)
    assert shortcut_refresh._appimage_version(Path("Soberix-1.10.0-x86_64.AppImage")) == (1, 10, 0)


def test_appimage_version_ignora_arquivo_alheio(tmp_path):
    assert shortcut_refresh._appimage_version(tmp_path / "blunix-1.0-x86_64.AppImage") is None
    assert shortcut_refresh._appimage_version(tmp_path / "app.txt") is None


# ---------------------------------------------------------------- find_newer
@pytest.fixture
def refresh_env(tmp_path, monkeypatch):
    apps = tmp_path / "applications"
    apps.mkdir()
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    monkeypatch.setattr(desktop_integration, "APPS_DIR", apps)
    monkeypatch.setattr(shortcut_refresh, "DOWNLOAD_DIRS", (downloads,))
    # sem APPIMAGE por padrão (roda do código): refresh_shortcut não deve agir
    monkeypatch.delenv("APPIMAGE", raising=False)
    return {"apps": apps, "downloads": downloads, "tmp": tmp_path, "monkeypatch": monkeypatch}


def _install_old_shortcut(refresh_env, version="1.3"):
    desktop = refresh_env["apps"] / f"{desktop_integration.DESKTOP_ID}.desktop"
    desktop.write_text(
        f"[Desktop Entry]\nType=Application\nName=Soberix\n"
        f"Exec=/x/Soberix-{version}-x86_64.AppImage\n",
        encoding="utf-8",
    )
    return desktop


def test_find_newer_sem_atalho_instalado(refresh_env):
    # nada instalado: não há referencial -> nada a fazer (nem crash)
    assert shortcut_refresh.find_newer_appimage() is None


def test_find_newer_encontra_versao_maior(refresh_env):
    _install_old_shortcut(refresh_env, "1.3")
    _make_appimage(refresh_env["downloads"], "1.4.1")
    _make_appimage(refresh_env["downloads"], "1.4")  # mais novo que atalho, mais velho que 1.4.1
    found = shortcut_refresh.find_newer_appimage()
    assert found is not None and found.name == "Soberix-1.4.1-x86_64.AppImage"


def test_find_newer_nada_mais_novo(refresh_env):
    _install_old_shortcut(refresh_env, "1.4.1")
    _make_appimage(refresh_env["downloads"], "1.4")
    assert shortcut_refresh.find_newer_appimage() is None


# ---------------------------------------------------------------- refresh_shortcut
def test_refresh_nao_faz_nada_fora_de_appimage(refresh_env):
    _install_old_shortcut(refresh_env, "1.3")
    _make_appimage(refresh_env["downloads"], "1.4.1")
    assert shortcut_refresh.refresh_shortcut() is None


def test_refresh_reaponta_para_o_mais_novo(refresh_env):
    desktop = _install_old_shortcut(refresh_env, "1.3")
    newer = _make_appimage(refresh_env["downloads"], "1.4.1")
    refresh_env["monkeypatch"].setenv("APPIMAGE", str(newer))

    upd = shortcut_refresh.refresh_shortcut()
    assert upd is not None
    assert upd.new_version == "1.4.1"
    assert upd.new_exec == str(newer)
    assert "Soberix-1.3" in upd.old_exec

    text = desktop.read_text(encoding="utf-8")
    exec_line = next(l for l in text.splitlines() if l.startswith("Exec="))
    assert exec_line == f"Exec={newer}"

    # idempotente: rodar de novo não muda mais nada (atalho já é o mais novo)
    upd2 = shortcut_refresh.refresh_shortcut()
    assert upd2 is None


def test_refresh_preserva_appimage_env_do_processo(refresh_env):
    """O env APPIMAGE do processo atual deve ser restaurado após o refresh."""
    newer = _make_appimage(refresh_env["downloads"], "1.4.1")
    _install_old_shortcut(refresh_env, "1.3")
    refresh_env["monkeypatch"].setenv("APPIMAGE", str(newer))
    shortcut_refresh.refresh_shortcut()
    import os
    assert os.environ["APPIMAGE"] == str(newer)
