import io
import zipfile
from pathlib import Path

import pytest

from soberix import constants, mods


@pytest.fixture(autouse=True)
def overlay(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "asset_overlay"
    monkeypatch.setattr(constants, "SOBER_ASSET_OVERLAY", root)
    return root


def _zip(names: dict[str, bytes], tmp_path: Path) -> Path:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in names.items():
            zf.writestr(name, data)
    p = tmp_path / "mod.zip"
    p.write_bytes(buf.getvalue())
    return p


def test_install_zip_preserves_structure(overlay: Path, tmp_path: Path):
    z = _zip({"content/textures/Cursors/KeyboardMouse/ArrowCursor.png": b"png-bytes"}, tmp_path)
    installed = mods.install_zip(z)
    assert installed == ["content/textures/Cursors/KeyboardMouse/ArrowCursor.png"]
    assert (overlay / "content/textures/Cursors/KeyboardMouse/ArrowCursor.png").read_bytes() == b"png-bytes"


def test_install_rejects_zip_slip(overlay: Path, tmp_path: Path):
    z = _zip({"../evil.txt": b"x"}, tmp_path)
    with pytest.raises(mods.ModError):
        mods.install_zip(z)
    assert list(overlay.rglob("*")) == [] or not overlay.exists()


def test_install_rejects_blocked_prefix(overlay: Path, tmp_path: Path):
    z = _zip({"scripts/whatever.lua": b"x"}, tmp_path)
    with pytest.raises(mods.ModError):
        mods.install_zip(z)


def test_install_rejects_bad_extension(overlay: Path, tmp_path: Path):
    z = _zip({"content/textures/evil.exe": b"x"}, tmp_path)
    with pytest.raises(mods.ModError):
        mods.install_zip(z)


def test_list_and_remove(overlay: Path, tmp_path: Path):
    z = _zip({"content/a.png": b"1", "content/b/c.wav": b"2"}, tmp_path)
    mods.install_zip(z)
    rels = [m.rel_path for m in mods.list_mods()]
    assert rels == ["content/a.png", "content/b/c.wav"]
    assert mods.remove_path("content/b/c.wav") is True
    # pasta vazia b/ é limpa
    assert not (overlay / "content/b").exists()
    assert [m.rel_path for m in mods.list_mods()] == ["content/a.png"]


def test_clear_all(overlay: Path, tmp_path: Path):
    mods.install_zip(_zip({"content/a.png": b"1"}, tmp_path))
    assert mods.clear_all() == 1
    assert mods.list_mods() == []
