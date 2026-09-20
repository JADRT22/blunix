"""Verificação de ambiente (doctor) para rodar Sober + Blunix.

Requisitos do Sober (https://vinegarhq.org/Sober/FAQ/index.html):
- CPU x86_64 com SSE4.1 e SSE4.2
- GPU com Vulkan (fallback OpenGL no Sober)
- Flatpak com o Sober instalado
"""
from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import constants


class Status(Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class Check:
    name: str
    status: Status
    detail: str


def _flatpak_installed() -> bool:
    return shutil.which("flatpak") is not None


def _flatpak_app_installed(app_id: str) -> bool:
    try:
        out = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application"],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return False
    return app_id in out.split()


def _sober_version() -> str | None:
    try:
        out = subprocess.run(
            ["flatpak", "info", constants.FLATPAK_APP_ID],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    for line in out.splitlines():
        if line.strip().startswith("Version:"):
            return line.split(":", 1)[1].strip() or None
    return None


def _cpu_flags() -> set[str]:
    flags: set[str] = set()
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("flags"):
                flags.update(line.split(":", 1)[1].split())
                break
    except OSError:
        pass
    return flags


def _vulkaninfo_available() -> bool:
    return shutil.which("vulkaninfo") is not None


def run_checks() -> list[Check]:
    checks: list[Check] = []

    arch = platform.machine()
    checks.append(Check(
        "Arquitetura",
        Status.OK if arch == "x86_64" else Status.WARN,
        f"{arch}" + ("" if arch == "x86_64" else " (Sober oficial é x86_64; ARM é beta)"),
    ))

    flags = _cpu_flags()
    sse = all(f in flags for f in ("sse4_1", "sse4_2"))
    checks.append(Check(
        "CPU SSE4.1/4.2",
        Status.OK if sse else Status.FAIL,
        "presentes" if sse else "AUSENTES — o Sober não vai rodar",
    ))

    checks.append(Check(
        "Flatpak",
        Status.OK if _flatpak_installed() else Status.FAIL,
        "instalado" if _flatpak_installed() else "não encontrado no PATH",
    ))

    if _flatpak_installed():
        installed = _flatpak_app_installed(constants.FLATPAK_APP_ID)
        ver = _sober_version() if installed else None
        checks.append(Check(
            "Sober",
            Status.OK if installed else Status.FAIL,
            f"instalado (versão {ver})" if ver else
            ("instalado" if installed else f"não instalado — 'flatpak install flathub {constants.FLATPAK_APP_ID}'"),
        ))
    else:
        checks.append(Check("Sober", Status.FAIL, "impossível verificar sem flatpak"))

    if _vulkaninfo_available():
        try:
            ok = subprocess.run(
                ["vulkaninfo", "--summary"],
                capture_output=True, text=True, timeout=15,
            ).returncode == 0
        except OSError:
            ok = False
        checks.append(Check(
            "Vulkan",
            Status.OK if ok else Status.WARN,
            "disponível" if ok else "presente mas falhou (Sober cai p/ OpenGL)",
        ))
    else:
        checks.append(Check(
            "Vulkan",
            Status.WARN,
            "vulkaninfo não instalado — não dá para verificar (Sober usa OpenGL como fallback)",
        ))

    cfg = constants.SOBER_CONFIG_FILE
    checks.append(Check(
        "Config do Sober",
        Status.OK if cfg.is_file() else Status.WARN,
        str(cfg) if cfg.is_file() else "ainda não existe (criada no 1º boot do Sober)",
    ))

    return checks


def all_ok(checks: list[Check]) -> bool:
    return all(c.status != Status.FAIL for c in checks)
