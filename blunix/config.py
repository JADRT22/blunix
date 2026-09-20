"""Leitura e escrita do config.json do Sober.

O arquivo do Sober pode conter comentários `//` no topo, então toleramos
linhas de comentário ao ler (estilo JSON5 mínimo). Toda escrita primeiro faz
backup do arquivo atual em ~/.local/share/blunix/backups/.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import time
from pathlib import Path
from typing import Any

from . import constants

log = logging.getLogger(__name__)

# Schema oficial: https://vinegarhq.org/Sober/Configuration/index.html
CONFIG_SCHEMA: dict[str, dict[str, Any]] = {
    "allow_gamepad_permission": {"type": bool, "default": False},
    "close_on_leave": {"type": bool, "default": True},
    "discord_rpc_enabled": {"type": bool, "default": False},
    "discord_rpc_show_join_button": {"type": bool, "default": False},
    "enable_gamemode": {"type": bool, "default": True},
    "enable_hidpi": {"type": bool, "default": False},
    "enable_mobile_home_screen": {"type": bool, "default": False},
    "fflags": {"type": dict, "default": {}},
    "graphics_optimization_mode": {
        "type": str,
        "default": "balanced",
        "choices": ("quality", "balanced", "performance"),
    },
    "server_location_indicator_enabled": {"type": bool, "default": False},
    "touch_mode": {
        "type": str,
        "default": "off",
        "choices": ("off", "on", "fake-off"),
    },
    "use_console_experience": {"type": bool, "default": False},
    "use_libsecret": {"type": bool, "default": False},
    "use_opengl": {"type": bool, "default": False},
}

_BOOL_RE = re.compile(r"\b(true|false)\b")


def _strip_comments(text: str) -> str:
    """Remove comentários // (apenas em linhas cujo início os contenha antes de conteúdo JSON relevante).

    O Sober escreve cabeçalhos com '//' no começo da linha; nós os removemos de
    forma conservadora: linhas que, após strip, começam com '//'.
    """
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        kept.append(line)
    return "\n".join(kept)


def parse_config_text(text: str) -> dict[str, Any]:
    """Faz parse do config.json do Sober tolerando comentários de cabeçalho."""
    cleaned = _strip_comments(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Alguns arquivos têm vírgulas finais; tenta remover vírgulas antes de } ou ]
        cleaned2 = re.sub(r",(\s*[}\]])", r"\1", cleaned)
        data = json.loads(cleaned2)  # pode levantar de novo: erro real
    if not isinstance(data, dict):
        raise ValueError("config.json não contém um objeto JSON")
    return data


def read_config(path: Path | None = None) -> dict[str, Any]:
    """Lê o config do Sober, preenchendo defaults do schema quando ausentes."""
    cfg_path = path or constants.SOBER_CONFIG_FILE
    result: dict[str, Any] = {k: v["default"] for k, v in CONFIG_SCHEMA.items()}
    if not cfg_path.exists():
        log.warning("Config do Sober não encontrada em %s (usando defaults)", cfg_path)
        return result
    data = parse_config_text(cfg_path.read_text(encoding="utf-8"))
    for key, value in data.items():
        result[key] = value
    return result


def _backup_current(cfg_path: Path) -> Path | None:
    if not cfg_path.exists():
        return None
    from .backups import create_backup  # import tardio evita ciclo

    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = constants.BLUNIX_BACKUP_DIR / f"config-prewrite-{stamp}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cfg_path, dest)
    log.debug("Backup pré-escrita em %s", dest)
    return dest


def _serialize(data: dict[str, Any]) -> str:
    header = (
        "// Editado pelo Blunix. Documentação: "
        + constants.VINEGAR_DOCS
        + "\n"
    )
    body = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)
    return header + body + "\n"


def validate_value(key: str, value: Any) -> Any:
    """Valida e converte `value` para o schema; levanta ValueError se inválido."""
    spec = CONFIG_SCHEMA.get(key)
    if spec is None:
        raise ValueError(
            f"Chave desconhecida: {key!r}. Chaves válidas: {', '.join(sorted(CONFIG_SCHEMA))}"
        )
    expected = spec["type"]
    if expected is bool and isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "1", "yes", "sim"):
            return True
        if low in ("false", "0", "no", "nao", "não"):
            return False
        raise ValueError(f"Valor booleano inválido para {key}: {value!r}")
    if expected is int and isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    if expected is dict:
        if not isinstance(value, dict):
            raise ValueError(f"{key} deve ser um objeto/dicionário")
        return value
    if not isinstance(value, expected):
        raise ValueError(
            f"{key} espera {expected.__name__}, recebeu {type(value).__name__}"
        )
    if "choices" in spec and value not in spec["choices"]:
        raise ValueError(
            f"{key} deve ser um de: {', '.join(spec['choices'])} (recebeu {value!r})"
        )
    return value


def write_config(
    updates: dict[str, Any],
    path: Path | None = None,
    *,
    create_backup: bool = True,
) -> Path:
    """Aplica updates sobre a config atual e reescreve o arquivo.

    Retorna o caminho escrito. Levanta ValueError para chave/valor inválidos.
    """
    cfg_path = path or constants.SOBER_CONFIG_FILE
    current = read_config(cfg_path)
    for key, value in updates.items():
        current[key] = validate_value(key, value)
    # Remove chaves desconhecidas para não quebrar o Sober? Não: preservamos
    # chaves estranhas que o próprio Sober possa ter adicionado.
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if create_backup:
        _backup_current(cfg_path)
    tmp = cfg_path.with_suffix(".json.blunix-tmp")
    tmp.write_text(_serialize(current), encoding="utf-8")
    tmp.replace(cfg_path)
    log.info("Config escrita em %s: %s", cfg_path, ", ".join(updates) or "(sem mudanças)")
    return cfg_path


def set_value(key: str, value: Any, path: Path | None = None) -> Path:
    return write_config({key: value}, path)
