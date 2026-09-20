from pathlib import Path

import pytest

from blunix import desktop_integration, launcher


# ---------------------------------------------------------------- extract_place_id
def test_place_id_puro():
    assert launcher.extract_place_id("2753915549") == "2753915549"
    assert launcher.extract_place_id(" 1818 ") == "1818"


def test_place_id_de_link_roblox():
    assert launcher.extract_place_id("roblox://experiences/start?placeId=1818") == "1818"
    deep = "roblox-player:1+launchmode:gameplace+placeid:1234+launchtime:0"
    assert launcher.extract_place_id(deep) == "1234"


def test_place_id_de_url_do_site():
    url = "https://www.roblox.com/games/2753915549/Brookhaven-RP"
    assert launcher.extract_place_id(url) == "2753915549"


def test_place_id_vazio_e_none():
    assert launcher.extract_place_id(None) is None
    assert launcher.extract_place_id("   ") is None


def test_place_id_lixo_levanta_erro():
    with pytest.raises(launcher.LaunchError):
        launcher.extract_place_id("joga um jogo ai")


def test_launch_aceita_url_do_site(monkeypatch):
    captured = {}

    def fake_popen(cmd, **kw):
        captured["cmd"] = cmd

        class P:
            pass

        return P()

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    launcher.launch("https://www.roblox.com/games/999/Teste")
    assert captured["cmd"][-1] == "roblox://experiences/start?placeId=999"


# ---------------------------------------------------------------- menu de aplicativos
@pytest.fixture
def menu_paths(tmp_path: Path, monkeypatch):
    apps = tmp_path / "applications"
    hicolor = tmp_path / "icons" / "hicolor"
    monkeypatch.setattr(desktop_integration, "APPS_DIR", apps)
    monkeypatch.setattr(desktop_integration, "HICOLOR_BASE", hicolor)
    monkeypatch.setattr(desktop_integration, "ICONS_DIR", hicolor / "256x256/apps")
    return {"apps": apps, "icons": hicolor}


def test_install_and_uninstall_menu(menu_paths):
    result = desktop_integration.install_menu()
    assert result.desktop_path.exists()
    assert "Exec=" in result.desktop_path.read_text(encoding="utf-8")
    assert desktop_integration.is_menu_installed()
    # Icon= deve ser caminho estável dentro do HOME ou nome no tema —
    # nunca /tmp/.mount_... (que morre quando o AppImage desmonta)
    icon_line = next(
        l for l in result.desktop_path.read_text(encoding="utf-8").splitlines()
        if l.startswith("Icon=")
    )
    assert icon_line.startswith(f"Icon={menu_paths['icons']}") or icon_line == f"Icon={desktop_integration.DESKTOP_ID}"
    # ícones instalados nos tamanhos (dentro do tmp isolado)
    assert result.icon_path is not None and result.icon_path.exists()
    assert desktop_integration.uninstall_menu() is True
    assert not desktop_integration.is_menu_installed()
    assert not result.icon_path.exists()


def test_uninstall_sem_install(menu_paths):
    assert desktop_integration.uninstall_menu() is False
