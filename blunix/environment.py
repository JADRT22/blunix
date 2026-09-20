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
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import constants
from .i18n import t


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


_CACHE: tuple[float, list[Check]] | None = None


def run_checks(*, use_cache: bool = True) -> list[Check]:
    """Roda as checagens; com cache de 30s (subprocessos custam até dezenas de s).

    use_cache=False força reexecução (botão 'Verificar de novo').
    """
    global _CACHE
    if use_cache and _CACHE is not None:
        ts, value = _CACHE
        if (time.monotonic() - ts) < 30.0:
            return value
    result = _run_checks_uncached()
    _CACHE = (time.monotonic(), result)
    return result


def _run_checks_uncached() -> list[Check]:
    checks: list[Check] = []

    arch = platform.machine()
    checks.append(Check(
        t("chk.arch"),
        Status.OK if arch == "x86_64" else Status.WARN,
        arch + ("" if arch == "x86_64" else t("chk.arch.arm")),
    ))

    flags = _cpu_flags()
    sse = all(f in flags for f in ("sse4_1", "sse4_2"))
    checks.append(Check(
        t("chk.sse"),
        Status.OK if sse else Status.FAIL,
        t("chk.sse.ok") if sse else t("chk.sse.fail"),
    ))

    flatpak = _flatpak_installed()
    checks.append(Check(
        t("chk.flatpak"),
        Status.OK if flatpak else Status.FAIL,
        t("chk.flatpak.ok") if flatpak else t("chk.flatpak.fail"),
    ))

    if flatpak:
        installed = _flatpak_app_installed(constants.FLATPAK_APP_ID)
        ver = _sober_version() if installed else None
        checks.append(Check(
            t("chk.sober"),
            Status.OK if installed else Status.FAIL,
            t("chk.sober.ok", ver=ver) if ver else
            (t("chk.sober.ok_nover") if installed else t("chk.sober.fail", app_id=constants.FLATPAK_APP_ID)),
        ))
    else:
        checks.append(Check(t("chk.sober"), Status.FAIL, t("chk.sober.unknown")))

    if _vulkaninfo_available():
        try:
            ok = subprocess.run(
                ["vulkaninfo", "--summary"],
                capture_output=True, text=True, timeout=15,
            ).returncode == 0
        except OSError:
            ok = False
        checks.append(Check(
            t("chk.vulkan"),
            Status.OK if ok else Status.WARN,
            t("chk.vulkan.ok") if ok else t("chk.vulkan.warn_fail"),
        ))
    else:
        checks.append(Check(
            t("chk.vulkan"),
            Status.WARN,
            t("chk.vulkan.warn_missing"),
        ))

    cfg = constants.SOBER_CONFIG_FILE
    checks.append(Check(
        t("chk.cfg"),
        Status.OK if cfg.is_file() else Status.WARN,
        t("chk.cfg.ok") if cfg.is_file() else t("chk.cfg.warn"),
    ))

    return checks


def all_ok(checks: list[Check]) -> bool:
    return all(c.status != Status.FAIL for c in checks)
