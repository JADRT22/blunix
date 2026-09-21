"""Constantes centrais do Soberix."""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Soberix"
APP_ID = "com.github.fernando.soberix"
VERSION = "1.5.1"

FLATPAK_APP_ID = "org.vinegarhq.Sober"
FLATPAK_REF = f"app/{FLATPAK_APP_ID}/x86_64/stable"
SOBER_DESKTOP_ID = FLATPAK_APP_ID

VINEGAR_DOCS = "https://vinegarhq.org/Sober/Configuration/index.html"
TIPS_DOCS = "https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html"
SOBER_SITE = "https://sober.vinegarhq.org/"
FLATHUB_URL = f"https://flathub.org/apps/{FLATPAK_APP_ID}"

def _xdg(var: str, fallback: Path) -> Path:
    return Path(os.environ.get(var) or (Path.home() / fallback))

# Base do Sober (flatpak per-user ou por-máquina)
def _sober_var_base() -> Path:
    user_base = Path.home() / ".var/app" / FLATPAK_APP_ID
    if user_base.is_dir():
        return user_base
    return Path("/var/lib/flatpak") / FLATPAK_APP_ID

SOBER_VAR_BASE = _sober_var_base()
SOBER_CONFIG_DIR = SOBER_VAR_BASE / "config" / "sober"
SOBER_CONFIG_FILE = SOBER_CONFIG_DIR / "config.json"
SOBER_DATA_DIR = SOBER_VAR_BASE / "data" / "sober"
SOBER_ASSET_OVERLAY = SOBER_DATA_DIR / "asset_overlay"
SOBER_LOG_DIR = SOBER_DATA_DIR / "sober_logs"
SOBER_LATEST_LOG = SOBER_LOG_DIR / "latest.log"

# Dados do Soberix
SOBERIX_DATA_DIR = _xdg("XDG_DATA_HOME", Path(".local/share")) / "soberix"
SOBERIX_STATE_DIR = _xdg("XDG_STATE_HOME", Path(".local/state")) / "soberix"
SOBERIX_BACKUP_DIR = SOBERIX_DATA_DIR / "backups"
SOBERIX_LOG_FILE = SOBERIX_STATE_DIR / "soberix.log"

# Presets de FastFlags (allowlist pós-2025-09-30; ver TipsAndTricks)
# "leve/medio/completo" = o quanto muda no visual, do menor pro maior impacto.
FFLAG_PRESETS: dict[str, dict[str, object]] = {
    "leve": {
        "FIntDebugForceMSAASamples": 1,
        "DFFlagTextureQualityOverrideEnabled": True,
        "DFIntTextureQualityOverride": 2,
        "FIntFRMMaxGrassDistance": 400,
    },
    "medio": {
        "FIntDebugForceMSAASamples": 1,
        "DFFlagTextureQualityOverrideEnabled": True,
        "DFIntTextureQualityOverride": 1,
        "DFIntDebugFRMQualityLevelOverride": 5,
        "DFIntCSGLevelOfDetailSwitchingDistance": 100,
        "DFIntCSGLevelOfDetailSwitchingDistanceL12": 75,
        "DFIntCSGLevelOfDetailSwitchingDistanceL23": 100,
        "DFIntCSGLevelOfDetailSwitchingDistanceL34": 150,
        "FIntFRMMaxGrassDistance": 150,
        "FIntFRMMinGrassDistance": 0,
    },
    "completo": {
        "FIntDebugForceMSAASamples": 1,
        "DFFlagTextureQualityOverrideEnabled": True,
        "DFIntTextureQualityOverride": 0,
        "DFIntDebugFRMQualityLevelOverride": 1,
        "DFFlagDebugPauseVoxelizer": True,
        "FFlagDebugSkyGray": True,
        "DFIntCSGLevelOfDetailSwitchingDistance": 1,
        "DFIntCSGLevelOfDetailSwitchingDistanceL12": 1,
        "DFIntCSGLevelOfDetailSwitchingDistanceL23": 1,
        "DFIntCSGLevelOfDetailSwitchingDistanceL34": 1,
        "FIntFRMMaxGrassDistance": 0,
        "FIntFRMMinGrassDistance": 0,
    },
    "default": {},
}

# Texto simples do que cada preset muda (mostrado na GUI/CLI)
PRESET_DESCRIPTIONS: dict[str, str] = {
    "leve": "Muda pouco: anti-aliasing desligado e texturas um pouco mais leves; "
            "grama visível só até 400 studs. Visual quase igual, FPS um pouco melhor.",
    "medio": "Equilibrado: texturas leves, sombreamento reduzido, detalhes de CSG "
             "simplificados e grama curta. Bom ganho de FPS mantendo o jogo bonito.",
    "completo": "Muda muito: foco total em FPS — iluminação simples, céu cinza, "
                "texturas mínimas, grama removida e LOD agressivo. Visual bem diferente.",
    "default": "Limpa todas as flags de preset e volta ao comportamento padrão do Sober.",
}

# Preset aplicado antes de qualquer preset (limpa flags do preset oposto)
PRESET_RESET_KEYS = sorted(
    {key for preset in FFLAG_PRESETS.values() for key in preset}
)
