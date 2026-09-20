import json
from pathlib import Path

import pytest

from soberix import backups, config, constants


@pytest.fixture(autouse=True)
def paths():
    """Cria config vazia (o conftest já isola os caminhos em tmp_path)."""
    cfg = constants.SOBER_CONFIG_FILE
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("{}", encoding="utf-8")
    return {"cfg": cfg, "backups": constants.SOBERIX_BACKUP_DIR}


def test_create_and_list(paths):
    info = backups.create_backup()
    assert info.path.exists()
    listed = backups.list_backups()
    assert [i.path for i in listed] == [info.path]


def test_create_backup_missing_config_raises(paths):
    paths["cfg"].unlink()
    with pytest.raises(FileNotFoundError):
        backups.create_backup()


def test_restore(paths):
    paths["cfg"].write_text(json.dumps({"close_on_leave": True}), encoding="utf-8")
    info = backups.create_backup()
    paths["cfg"].write_text(json.dumps({"close_on_leave": False}), encoding="utf-8")
    backups.restore_backup(info.path.name)
    data = config.parse_config_text(paths["cfg"].read_text(encoding="utf-8"))
    assert data["close_on_leave"] is True
    # criou backup pré-restore
    stamps = [i.path.name for i in backups.list_backups()]
    assert any("pre-restore" in s for s in stamps)


def test_restore_rejects_corrupted(paths):
    info = backups.create_backup()
    info.path.write_text("{ isto não é json", encoding="utf-8")
    with pytest.raises(Exception):
        backups.restore_backup(info.path.name)


def test_prune(paths):
    for _ in range(5):
        backups.create_backup()
    removed = backups.prune(keep=2)
    assert removed == 3
    assert len(backups.list_backups()) == 2
