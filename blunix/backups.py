"""Backups do config.json do Sober.

Backups ficam em ~/.local/share/blunix/backups/ e incluem apenas config.json
(nunca cookies nem estado de sessão).
"""
from __future__ import annotations

import logging
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from . import config, constants

log = logging.getLogger(__name__)

STAMP_FMT = "%Y%m%d-%H%M%S"
STAMP_RE = re.compile(r"^\d{8}-\d{6}(\.\d+)?\.json$")


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    stamp: str


def _backup_dir() -> Path:
    constants.BLUNIX_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return constants.BLUNIX_BACKUP_DIR


def create_backup(label: str | None = None, cfg_path: Path | None = None) -> BackupInfo:
    """Copia o config.json atual para o diretório de backups."""
    cfg_path = cfg_path or constants.SOBER_CONFIG_FILE
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Config não encontrada: {cfg_path}")
    d = _backup_dir()
    stamp = time.strftime(STAMP_FMT)
    name = f"{stamp}.json" if not label else f"{stamp}-{label}.json"
    dest = d / name
    counter = 1
    while dest.exists():  # colisão de segundos: sufixo .1, .2... (bate com STAMP_RE)
        suffix = f"{stamp}.{counter}"
        name = f"{suffix}.json" if not label else f"{suffix}-{label}.json"
        dest = d / name
        counter += 1
    shutil.copy2(cfg_path, dest)
    log.info("Backup criado: %s", dest)
    return BackupInfo(path=dest, stamp=stamp)


def list_backups() -> list[BackupInfo]:
    d = constants.BLUNIX_BACKUP_DIR
    if not d.is_dir():
        return []
    infos = []
    for p in sorted(d.glob("*.json"), reverse=True):
        infos.append(BackupInfo(path=p, stamp=p.stem))
    return infos


def restore_backup(backup_path: Path, cfg_path: Path | None = None) -> Path:
    """Restaura um backup para o config.json do Sober (com backup prévio)."""
    backup_path = Path(backup_path)
    backup_path = backup_path if backup_path.is_absolute() else constants.BLUNIX_BACKUP_DIR / backup_path
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {backup_path}")
    cfg_path = cfg_path or constants.SOBER_CONFIG_FILE
    # sanity: precisa parsear antes de sobrescrever
    config.parse_config_text(backup_path.read_text(encoding="utf-8"))
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        stamp = time.strftime(STAMP_FMT)
        shutil.copy2(cfg_path, _backup_dir() / f"{stamp}-pre-restore.json")
    shutil.copy2(backup_path, cfg_path)
    log.info("Backup restaurado: %s -> %s", backup_path.name, cfg_path)
    return cfg_path


def prune(keep: int = 20) -> int:
    """Mantém só os `keep` backups mais recentes. Retorna quantos removeu."""
    backups = list_backups()
    removed = 0
    for info in backups[keep:]:
        info.path.unlink(missing_ok=True)
        removed += 1
    if removed:
        log.info("Pruned %d backups antigos", removed)
    return removed
