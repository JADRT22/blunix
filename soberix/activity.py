"""Activity tracking: detecta em que jogo/servidor o usuário está.

Fonte dos dados: os logs do próprio Sober (sober_logs/*.log). Sem acesso a
APIs privadas e sem tocar no cliente — apenas leitura de arquivo de log.

Linhas de interesse (verificadas em logs reais):

  ! Joining game '<jobId>' place <placeId> at <IP>          (servidor + IP)
  debug: rbx.jni: onGameLoaded() SessionReporterState_GameLoaded placeId:<id>
  info: Roblox: ... [FLog::GameJoinLoadTime] Report game_join_loadtime:
       sid:<sessionId>, ... placeid:<id>, userid:<u>, universeid:<uid>,

O arquivo `latest.log` é um symlink para o log da sessão corrente; cada
sessão do Sober cria um novo arquivo (a leitura por tail segue renomeações).
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import constants

_RE_JOINING = re.compile(
    r"Joining game '([0-9a-fA-F-]{8,})' place (\d+) at (\d+\.\d+\.\d+\.\d+)"
)
_RE_LOADED = re.compile(r"onGameLoaded\(\) SessionReporterState_GameLoaded placeId:(\d+)")
_RE_JOINTIME = re.compile(
    r"game_join_loadtime:.*?placeid:(\d+), userid:(\d+), universeid:(\d+)"
)
_RE_TS = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)")


def _line_ts(line: str) -> float | None:
    """Timestamp ISO (UTC) embutido nas linhas do Roblox, em epoch."""
    m = _RE_TS.search(line)
    if not m:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(m.group(1).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


@dataclass(frozen=True)
class Activity:
    place_id: str
    job_id: str | None = None      # id da instância de servidor (rejoin)
    universe_id: str | None = None
    server_ip: str | None = None
    started_ts: float = 0.0

    def as_dict(self) -> dict:
        return {
            "place_id": self.place_id,
            "job_id": self.job_id,
            "universe_id": self.universe_id,
            "server_ip": self.server_ip,
            "started_ts": self.started_ts,
        }


@dataclass(frozen=True)
class ServerLocation:
    city: str | None
    region: str | None
    country: str | None
    source_ip: str


def _latest_log() -> Path:
    return constants.SOBER_LATEST_LOG


def is_sober_running() -> bool:
    """True se existe processo do Sober (e não do Soberix) rodando."""
    import subprocess

    try:
        out = subprocess.run(
            ["pgrep", "-af", "sober"],
            capture_output=True, text=True, timeout=5, check=False,
        ).stdout
    except OSError:
        return False
    return any(
        line for line in out.splitlines()
        if "soberix" not in line and "pgrep" not in line and "sober" in line
    )


def _parse_log_text(text: str) -> Activity | None:
    """Extrai a atividade mais recente de um buffer de log completo."""
    act: Activity | None = None
    for line in text.splitlines():
        m = _RE_JOINING.search(line)
        if m:
            act = Activity(place_id=m.group(2), job_id=m.group(1),
                           server_ip=m.group(3), started_ts=_line_ts(line) or time.time())
            continue
        m = _RE_LOADED.search(line)
        if m and (act is None or act.place_id != m.group(1)):
            act = Activity(place_id=m.group(1), job_id=act.job_id if act else None,
                           universe_id=act.universe_id if act else None,
                           server_ip=act.server_ip if act else None,
                           started_ts=act.started_ts if act else time.time())
            continue
        m = _RE_JOINTIME.search(line)
        if m and act is not None and act.place_id == m.group(1):
            act = Activity(place_id=act.place_id, job_id=act.job_id,
                           universe_id=m.group(3), server_ip=act.server_ip,
                           started_ts=act.started_ts)
    return act


def activity_from_log(path: Path | None = None) -> Activity | None:
    """Lê o log da sessão corrente e retorna a atividade mais recente."""
    path = path or _latest_log()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return _parse_log_text(text)


def _scan_logs(log_dir: Path | None = None) -> list[Path]:
    """Logs de sessão ordenados do mais recente para o mais antigo."""
    d = log_dir or constants.SOBER_LOG_DIR
    try:
        candidates = [p for p in d.glob("*.log") if p.is_file() and not p.is_symlink()]
        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []


def recent_server_activity(log_dir: Path | None = None, *, max_files: int = 10) -> Activity | None:
    """Último jogo/servidor visto nos logs — funciona mesmo com o Sober fechado.

    O latest.log morre quando a sessão fecha; para "reentrar no último
    servidor" depois de fechar o jogo, varremos as sessões mais recentes
    (mais nova -> mais antiga) até achar a primeira com um join registrado.
    """
    act = activity_from_log()
    if act is not None:
        return act
    for log in _scan_logs(log_dir)[:max_files]:
        act = activity_from_log(log)
        if act is not None:
            return act
    return None


class ActivityWatcher:
    """Faz tail do latest.log em background e publica mudanças de atividade.

    Uso na GUI:
        watcher = ActivityWatcher(on_change=lambda act: GLib.idle_add(...))
        watcher.start()
        ...
        watcher.stop()
    """

    POLL_SECONDS = 2.0

    def __init__(self, on_change=None, on_game_loaded=None):
        self.on_change = on_change          # callable(Activity | None)
        self.on_game_loaded = on_game_loaded  # callable(Activity) — 1× por servidor
        self.current: Activity | None = None
        self._last_recorded: tuple[str, str | None] | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="soberix-activity")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _run(self) -> None:
        pos = 0
        buf = ""
        cur_file: str = ""
        while not self._stop.is_set():
            self._stop.wait(self.POLL_SECONDS)
            if self._stop.is_set():
                break
            log = _latest_log()
            try:
                if str(log) != cur_file:
                    cur_file = str(log)
                    pos = 0
                    buf = ""
                if log.is_file():
                    size = log.stat().st_size
                    if size < pos:  # truncado/recriado
                        pos = 0
                        buf = ""
                    if size > pos:
                        with open(log, encoding="utf-8", errors="replace") as f:
                            f.seek(pos)
                            chunk = f.read()
                            pos = f.tell()
                        buf = (buf + chunk)[-200_000:]  # teto de memória
                        act = _parse_log_text(buf)
                        if act != self.current:
                            self.current = act
                            if self.on_change:
                                try:
                                    self.on_change(act)
                                except Exception:  # noqa: BLE001
                                    pass
                        # grava no histórico 1× por (jogo, servidor) novo
                        if act is not None and self.on_game_loaded:
                            key = (act.place_id, act.job_id)
                            if key != self._last_recorded:
                                self._last_recorded = key
                                try:
                                    self.on_game_loaded(act)
                                except Exception:  # noqa: BLE001
                                    pass
            except OSError:
                continue


# ---------------------------------------------------------------- servidor (rejoin/localização)
def rejoin_url(act: Activity | None = None) -> str | None:
    """Deep link para reentrar no servidor atual/último (requer job_id)."""
    act = act or activity_from_log()
    if not act or not act.job_id:
        return None
    return (f"roblox://experiences/start?placeId={act.place_id}"
            f"&gameInstanceId={act.job_id}")


def copy_rejoin_link(act: Activity | None = None) -> bool:
    """Copia o link de rejoin para o clipboard (best effort)."""
    url = rejoin_url(act)
    if not url:
        return False
    try:
        subprocess_mod = __import__("subprocess")
        # Wayland/X11: wl-copy | xclip | xsel
        for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"]):
            try:
                proc = subprocess_mod.run(cmd, input=url.encode(),
                                          capture_output=True, timeout=5)
                if proc.returncode == 0:
                    return True
            except (OSError, subprocess_mod.SubprocessError):
                continue
    except Exception:  # noqa: BLE001
        return False
    return False


def _is_private_ip(ip: str) -> bool:
    """RFC1918/loopback: o ipinfo não geolocaliza endereços internos.

    Nos logs do Sober, o IP do servidor frequentemente é interno (10.x)
    — nesses casos a localização simplesmente não está disponível.
    """
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        return True
    o = [int(p) for p in parts]
    return (o[0] == 10 or o[0] == 127
            or (o[0] == 172 and 16 <= o[1] <= 31)
            or (o[0] == 192 and o[1] == 168))


def fetch_server_location(server_ip: str, timeout: float = 4.0) -> ServerLocation | None:
    """Consulta ipinfo.io (tier gratuito, sem chave) pelo IP do servidor."""
    import urllib.request

    if not server_ip or _is_private_ip(server_ip):
        return None
    try:
        req = urllib.request.Request(f"https://ipinfo.io/{server_ip}/json",
                                     headers={"Accept": "application/json",
                                              "User-Agent": "soberix/1.5"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("error") or not data.get("ip"):
        return None
    return ServerLocation(city=data.get("city"), region=data.get("region"),
                          country=data.get("country"), source_ip=server_ip)
