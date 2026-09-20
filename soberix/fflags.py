"""FastFlags: allowlist (pós 2025-09-30), validação e presets.

Fonte da allowlist: https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html
Flags fora dessa lista são ignoradas pelo cliente Roblox e, por isso, o
Soberix se recusa a escrevê-las (a menos que force=True).
"""
from __future__ import annotations

from typing import Any

from . import config, constants

# nome: (tipo python, descrição, valores permitidos ou None p/ intervalo)
ALLOWED_FFLAGS: dict[str, tuple[type, str, tuple | None]] = {
    # Geometria
    "DFIntCSGLevelOfDetailSwitchingDistance": (int, "LOD de CSG em studs", (0, 1000)),
    "DFIntCSGLevelOfDetailSwitchingDistanceL12": (int, "LOD CSG níveis 1-2", (0, 1000)),
    "DFIntCSGLevelOfDetailSwitchingDistanceL23": (int, "LOD CSG níveis 2-3", (0, 1000)),
    "DFIntCSGLevelOfDetailSwitchingDistanceL34": (int, "LOD CSG níveis 3-4", (0, 1000)),
    # Renderização
    "DFFlagTextureQualityOverrideEnabled": (bool, "Habilita override de textura", None),
    "DFIntTextureQualityOverride": (int, "Qualidade de textura 0-3", (0, 3)),
    "FIntDebugForceMSAASamples": (int, "Amostras MSAA (1/2/4)", (1, 2, 4)),
    "FFlagDebugSkyGray": (bool, "Céu cinza, sem estrelas", None),
    "DFFlagDebugPauseVoxelizer": (bool, "Desativa voxel lighting", None),
    "DFIntDebugFRMQualityLevelOverride": (int, "Override de qualidade gráfica", (0, 21)),
    "FIntFRMMaxGrassDistance": (int, "Distância máx. de grama (studs)", (0, 1000)),
    "FIntFRMMinGrassDistance": (int, "Distância mín. de grama (studs)", (0, 1000)),
    "FFlagDebugGraphicsPreferVulkan": (bool, "Prefere Vulkan (uso: config Force Legacy)", None),
    "FFlagDebugGraphicsPreferOpenGL": (bool, "Prefere OpenGL (uso: config Force Legacy)", None),
    "FFlagHandleAltEnterFullscreenManually": (bool, "Fullscreen manual (irrelevante no Sober)", None),
    "DFFlagDisableDPIScale": (bool, "Desativa DPI scaling (irrelevante no Sober)", None),
    # UI
    "FIntGrassMovementReducedMotionFactor": (bool, "Reduz movimento da grama", None),
}


class FFFlagError(ValueError):
    pass


def validate_flag(name: str, value: Any) -> Any:
    entry = ALLOWED_FFLAGS.get(name)
    if entry is None:
        raise FFFlagError(
            f"Flag {name!r} fora da allowlist pós-2025-09-30 e será ignorada pelo cliente. "
            f"Use 'fflags list' para ver as permitidas."
        )
    ftype, _desc, allowed = entry
    if ftype is bool and isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "1", "yes", "sim"):
            value = True
        elif low in ("false", "0", "no", "nao", "não"):
            value = False
        else:
            raise FFFlagError(f"Valor booleano inválido para {name}: {value!r}")
    if ftype is int and isinstance(value, str) and value.strip().lstrip("-").isdigit():
        value = int(value)
    if not isinstance(value, ftype):
        raise FFFlagError(
            f"{name} espera {ftype.__name__}, recebeu {type(value).__name__} ({value!r})"
        )
    if allowed is not None:
        if ftype is int and len(allowed) == 2 and isinstance(allowed[0], int) and isinstance(allowed[1], int):
            lo, hi = allowed
            if not (lo <= value <= hi):
                raise FFFlagError(f"{name} deve estar entre {lo} e {hi} (recebeu {value})")
        elif value not in allowed:
            raise FFFlagError(f"{name} deve ser um de: {', '.join(map(str, allowed))} (recebeu {value})")
    return value


def describe_allowed(name: str) -> str:
    """Descrição amigável dos valores aceitos por uma flag (ex.: '0..21', '1, 2, 4')."""
    ftype, _desc, allowed = ALLOWED_FFLAGS[name]
    if ftype is bool:
        return "true/false"
    if allowed is None:
        return "-"
    if (
        len(allowed) == 2
        and all(isinstance(a, int) for a in allowed)
        and allowed[1] - allowed[0] > 1
    ):
        return f"{allowed[0]}..{allowed[1]}"
    return ", ".join(map(str, allowed))


def current_fflags(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg if cfg is not None else config.read_config()
    fflags = cfg.get("fflags")
    return dict(fflags) if isinstance(fflags, dict) else {}


def set_flag(name: str, value: Any, *, force: bool = False) -> dict[str, Any]:
    """Define uma flag e escreve a config. Retorna as flags finais."""
    if not force:
        value = validate_flag(name, value)
    flags = current_fflags()
    flags[name] = value
    config.write_config({"fflags": flags})
    return flags


def remove_flag(name: str) -> dict[str, Any]:
    flags = current_fflags()
    if name in flags:
        del flags[name]
        config.write_config({"fflags": flags})
    return flags


def apply_preset(name: str) -> dict[str, Any]:
    """Aplica um preset (limpa chaves de presets antes, para não misturar)."""
    flags = stage_preset(name)
    config.write_config({"fflags": flags})
    return flags


def stage_preset(name: str) -> dict[str, Any]:
    """Calcula as flags resultantes de um preset SEM escrever no Sober.

    Usado pelo botão JOGAR: o perfil escolhido entra em vigor no momento em
    que o usuário joga pelo Soberix — abrir o Sober direto não é afetado.
    """
    if name not in constants.FFLAG_PRESETS:
        raise FFFlagError(
            f"Preset desconhecido: {name!r}. Disponíveis: {', '.join(sorted(constants.FFLAG_PRESETS))}"
        )
    preset = constants.FFLAG_PRESETS[name]
    return {
        k: v
        for k, v in current_fflags().items()
        if k not in constants.PRESET_RESET_KEYS
    } | dict(preset)
