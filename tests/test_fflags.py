import json
from pathlib import Path

import pytest

from blunix import config, constants, fflags


@pytest.fixture(autouse=True)
def sober_cfg() -> Path:
    """Cria config inicial (o conftest já isola o caminho em tmp_path)."""
    cfg = constants.SOBER_CONFIG_FILE
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps({"fflags": {}}), encoding="utf-8")
    return cfg


def test_validate_allows_whitelisted():
    assert fflags.validate_flag("DFIntTextureQualityOverride", 2) == 2
    assert fflags.validate_flag("FFlagDebugSkyGray", "true") is True


def test_validate_rejects_unknown_flag():
    with pytest.raises(fflags.FFFlagError):
        fflags.validate_flag("FFlagFakeFlagQueNaoExiste", True)


def test_validate_rejects_out_of_range():
    with pytest.raises(fflags.FFFlagError):
        fflags.validate_flag("DFIntTextureQualityOverride", 9)
    with pytest.raises(fflags.FFFlagError):
        fflags.validate_flag("FIntDebugForceMSAASamples", 3)  # só 1, 2 ou 4


def test_set_and_remove_flag(sober_cfg: Path):
    fflags.set_flag("FFlagDebugSkyGray", True)
    assert fflags.current_fflags()["FFlagDebugSkyGray"] is True
    fflags.remove_flag("FFlagDebugSkyGray")
    assert "FFlagDebugSkyGray" not in fflags.current_fflags()


def test_preset_completo(sober_cfg: Path):
    fflags.set_flag("DFIntTextureQualityOverride", 3)
    flags = fflags.apply_preset("completo")
    assert flags["DFIntTextureQualityOverride"] == 0
    assert flags["FIntDebugForceMSAASamples"] == 1
    assert flags["DFFlagDebugPauseVoxelizer"] is True
    # flag fora de preset permanece
    assert "FIntGrassMovementReducedMotionFactor" not in flags


def test_preset_leve_muda_pouco(sober_cfg: Path):
    flags = fflags.apply_preset("leve")
    assert len(flags) <= 4
    assert flags["FIntFRMMaxGrassDistance"] == 400  # grama continua visível


def test_preset_descriptions_cover_all():
    assert set(constants.PRESET_DESCRIPTIONS) == set(constants.FFLAG_PRESETS)


def test_preset_unknown_raises(sober_cfg: Path):
    with pytest.raises(fflags.FFFlagError):
        fflags.apply_preset("ultra")


def test_preserved_unknown_keys_in_config(sober_cfg: Path):
    """Chaves de config que o Blunix não conhece devem ser preservadas."""
    sober_cfg.write_text(json.dumps({"alguma_chave_futura": 42, "fflags": {}}), encoding="utf-8")
    fflags.set_flag("FFlagDebugSkyGray", True)
    data = config.parse_config_text(sober_cfg.read_text(encoding="utf-8"))
    assert data["alguma_chave_futura"] == 42
