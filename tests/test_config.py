import json
from pathlib import Path

import pytest

from soberix import config


@pytest.fixture
def cfg_file(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


def test_parse_config_with_header_comments():
    text = "// linha 1\n// linha 2\n{\"close_on_leave\": false}\n"
    data = config.parse_config_text(text)
    assert data == {"close_on_leave": False}


def test_read_config_fills_defaults(cfg_file: Path):
    cfg_file.write_text(json.dumps({"close_on_leave": False}), encoding="utf-8")
    cfg = config.read_config(cfg_file)
    assert cfg["close_on_leave"] is False
    assert cfg["enable_gamemode"] is True  # default do schema
    assert cfg["touch_mode"] == "off"


def test_read_config_missing_file_uses_defaults(cfg_file: Path):
    cfg = config.read_config(cfg_file)
    assert cfg["close_on_leave"] is True
    assert cfg["fflags"] == {}


def test_validate_bool_from_string():
    assert config.validate_value("close_on_leave", "true") is True
    assert config.validate_value("close_on_leave", "não") is False
    with pytest.raises(ValueError):
        config.validate_value("close_on_leave", "talvez")


def test_validate_choices():
    assert config.validate_value("touch_mode", "fake-off") == "fake-off"
    with pytest.raises(ValueError):
        config.validate_value("touch_mode", "sideways")


def test_validate_unknown_key():
    with pytest.raises(ValueError):
        config.validate_value("chave_inexistente", 1)


def test_write_config_roundtrip(cfg_file: Path):
    cfg_file.write_text(json.dumps({"enable_gamemode": True}), encoding="utf-8")
    config.write_config({"close_on_leave": False, "touch_mode": "on"}, cfg_file, create_backup=False)
    data = config.parse_config_text(cfg_file.read_text(encoding="utf-8"))
    assert data["close_on_leave"] is False
    assert data["touch_mode"] == "on"
    assert data["enable_gamemode"] is True  # preservado


def test_write_config_rejects_invalid(cfg_file: Path):
    with pytest.raises(ValueError):
        config.write_config({"touch_mode": "xyz"}, cfg_file, create_backup=False)
    assert not cfg_file.exists()  # nada foi escrito


def test_comment_header_written_by_soberix(cfg_file: Path):
    cfg_file.write_text("{}", encoding="utf-8")
    config.write_config({"use_opengl": True}, cfg_file, create_backup=False)
    text = cfg_file.read_text(encoding="utf-8")
    assert text.startswith("// Editado pelo Soberix")
    assert config.parse_config_text(text)["use_opengl"] is True
