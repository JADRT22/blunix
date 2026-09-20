"""Isolamento global: nenhum teste deve escrever no HOME real."""
import pytest

from soberix import constants


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    state_dir = tmp_path / "state"
    monkeypatch.setattr(constants, "SOBERIX_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(constants, "SOBERIX_STATE_DIR", state_dir)
    monkeypatch.setattr(constants, "SOBERIX_LOG_FILE", state_dir / "soberix.log")
    sober_cfg = tmp_path / "sober" / "config.json"
    monkeypatch.setattr(constants, "SOBER_CONFIG_FILE", sober_cfg)
    monkeypatch.setattr(constants, "SOBER_ASSET_OVERLAY", tmp_path / "asset_overlay")
    return tmp_path
