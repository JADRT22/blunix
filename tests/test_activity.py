"""Activity tracking: parse dos logs do Sober."""
from __future__ import annotations

from pathlib import Path

from soberix import activity

# Linhas reais (do log de 2026-09-20/21 do próprio ambiente de testes)
LINE_JOINING = (
    "info: Roblox: 2026-09-21T00:36:08.060Z,9.060396,385a06c0,6 [FLog::Output] "
    "! Joining game 'c67569c5-6580-4804-992b-ad7f7593bf8f' place 16205713724 at 10.221.32.150"
)
LINE_LOADED = (
    "debug: rbx.jni: onGameLoaded() SessionReporterState_GameLoaded placeId:16205713724"
)
LINE_JOINTIME = (
    "info: Roblox: 2026-09-21T00:36:08.060Z,9.060538,385a06c0,6 [FLog::GameJoinLoadTime] "
    "Report game_join_loadtime: sid:f2bc563c-5b2e-402b-a4c0-5fa91d0caea5, "
    "clienttime:1789950968.2409999371, join_time:0.54039714099999969221, referral_page:, "
    "placeid:16205713724, userid:9000081343, universeid:5595353122, "
)
LINE_OTHER = "info: app: lifecycle: logging_started delta=646.1485140025616ms"


def test_parse_joining_extrai_job_place_e_ip():
    act = activity._parse_log_text(LINE_JOINING)
    assert act is not None
    assert act.place_id == "16205713724"
    assert act.job_id == "c67569c5-6580-4804-992b-ad7f7593bf8f"
    assert act.server_ip == "10.221.32.150"


def test_parse_completo_inclui_universe_id():
    log = "\n".join([LINE_OTHER, LINE_JOINING, LINE_LOADED, LINE_JOINTIME])
    act = activity._parse_log_text(log)
    assert act is not None
    assert act.place_id == "16205713724"
    assert act.universe_id == "5595353122"


def test_parse_so_loaded_sem_job():
    act = activity._parse_log_text(LINE_LOADED)
    assert act is not None
    assert act.place_id == "16205713724"
    assert act.job_id is None


def test_parse_log_vazio_ou_irrelevante():
    assert activity._parse_log_text("") is None
    assert activity._parse_log_text(LINE_OTHER) is None


def test_teleport_para_outro_jogo_persistindo_job(tmp_path: Path):
    """Teleport: segundo Joining (novo jogo) vira a atividade corrente."""
    join2 = LINE_JOINING.replace("place 16205713724", "place 136406881576517")
    log = "\n".join([LINE_JOINING, join2])
    act = activity._parse_log_text(log)
    assert act is not None and act.place_id == "136406881576517"


def test_activity_from_log_lendo_arquivo(tmp_path: Path):
    log = tmp_path / "latest.log"
    log.write_text(LINE_OTHER + "\n" + LINE_JOINING + "\n", encoding="utf-8")
    act = activity.activity_from_log(log)
    assert act is not None and act.place_id == "16205713724"


def test_activity_from_log_arquivo_ausente(tmp_path: Path):
    assert activity.activity_from_log(tmp_path / "nada.log") is None


def test_rejoin_url_requer_job_id():
    from soberix.activity import Activity

    assert activity.rejoin_url(Activity(place_id="123", job_id=None)) is None
    url = activity.rejoin_url(Activity(place_id="123", job_id="abc-def"))
    assert url == "roblox://experiences/start?placeId=123&gameInstanceId=abc-def"


def test_recent_server_activity_escaneia_sessoes(tmp_path: Path, monkeypatch):
    """Após fechar o Sober, o último servidor vem dos logs de sessões passadas."""
    # latest.log inexistente (sessão fechada/removeu o symlink)
    monkeypatch.setattr(activity, "_latest_log", lambda: tmp_path / "inexistente.log")
    antigo = tmp_path / "2026-09-20_21-35-57.log"
    antigo.write_text(LINE_JOINING + "\n", encoding="utf-8")
    act = activity.recent_server_activity(log_dir=tmp_path)
    assert act is not None and act.job_id == "c67569c5-6580-4804-992b-ad7f7593bf8f"


def test_recent_server_activity_sem_logs(tmp_path: Path, monkeypatch):
    """Sem atividade corrente (latest.log ausente) e sem logs em tmp: None.

    O _latest_log real é isolado — senão o teste dependeria de o Sober
    estar rodando na máquina (log de sessão com join quebraria o teste).
    """
    monkeypatch.setattr(activity, "_latest_log", lambda: tmp_path / "inexistente.log")
    assert activity.recent_server_activity(log_dir=tmp_path) is None


# ---------------------------------------------------------------- nomes e histórico de servidores
def test_fetch_game_name_formata_apis(monkeypatch):
    """fetch_game_name encadeia universe API -> games API."""
    import json as _json
    from soberix import history

    calls = []

    class R:
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return _json.dumps(self.payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        if "universes/v1" in req.full_url:
            return R({"universeId": 5595353122})
        return R({"data": [{"name": "Brookhaven RP"}]})

    monkeypatch.setattr(history.urllib.request, "urlopen", fake_urlopen)
    assert history.fetch_game_name("136406881576517") == "Brookhaven RP"
    assert len(calls) == 2


def test_fetch_game_name_offline_retorna_none(monkeypatch):
    from soberix import history

    def boom(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr(history.urllib.request, "urlopen", boom)
    assert history.fetch_game_name("123") is None


def test_set_name_atualiza_recentes_e_servidores(tmp_path, monkeypatch):
    from soberix import history, constants

    monkeypatch.setattr(constants, "SOBERIX_STATE_DIR", tmp_path / "state")
    history.add_recent("111", name="111")
    history.add_server("111", "job-abc", name="111")
    history.set_name("111", "Brookhaven RP")
    assert history.recent()[0].name == "Brookhaven RP"
    assert history.server_history()[0]["name"] == "Brookhaven RP"


def test_remove_server(tmp_path, monkeypatch):
    from soberix import history, constants

    monkeypatch.setattr(constants, "SOBERIX_STATE_DIR", tmp_path / "state")
    history.add_server("222", "job-x")
    history.add_server("333", "job-y")
    assert history.remove_server("job-x") is True
    assert [s["job_id"] for s in history.server_history()] == ["job-y"]
    assert history.remove_server("nao-existe") is False
