"""CLI do Blunix (argparse, zero dependências externas)."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import config, constants, environment, fflags, launcher, mods, backups, desktop_integration, settings

log = logging.getLogger("blunix")

STATUS_ICON = {
    environment.Status.OK: "✔",
    environment.Status.WARN: "⚠",
    environment.Status.FAIL: "✘",
}


def _setup_logging(verbose: bool, log_to_file: bool = False) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_to_file:
        constants.BLUNIX_STATE_DIR.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(constants.BLUNIX_LOG_FILE, encoding="utf-8"))
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, handlers=handlers, format="%(levelname)s %(name)s: %(message)s")


def _print_checks() -> int:
    checks = environment.run_checks()
    width = max(len(c.name) for c in checks)
    for c in checks:
        icon = STATUS_ICON[c.status]
        print(f"  {icon} {c.name.ljust(width)}  {c.detail}")
    return 0 if environment.all_ok(checks) else 1


# ---------------------------------------------------------------- doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"{constants.APP_NAME} {constants.VERSION} — diagnóstico do ambiente")
    code = _print_checks()
    print()
    if code == 0:
        print("Tudo pronto para rodar o Sober.")
    else:
        print("Há problemas acima marcados com ✘ que impedem o Sober de rodar.")
    return code


# ---------------------------------------------------------------- config
def cmd_config_show(args: argparse.Namespace) -> int:
    cfg = config.read_config()
    if args.json:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
    else:
        for key in sorted(cfg):
            print(f"{key} = {cfg[key]!r}")
    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value  # deixa como string; validate_value converte bool/int
    try:
        config.set_value(args.key, value)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {args.key} = {value!r}")
    return 0


def cmd_config_reset(args: argparse.Namespace) -> int:
    defaults = {k: v["default"] for k, v in config.CONFIG_SCHEMA.items()}
    try:
        config.write_config(defaults, create_backup=True)
    except FileNotFoundError:
        print("Nada a resetar: config não existe.", file=sys.stderr)
        return 1
    print("Config restaurada aos defaults (backup criado).")
    return 0


# ---------------------------------------------------------------- fflags
def cmd_fflags_list(args: argparse.Namespace) -> int:
    current = fflags.current_fflags()
    if args.json:
        print(json.dumps(current, indent=2, ensure_ascii=False))
        return 0
    print("Flags da allowlist (post 2025-09-30):")
    for name, (ftype, desc, _allowed) in sorted(fflags.ALLOWED_FFLAGS.items()):
        marker = " [ativa]" if name in current else ""
        value = f" = {current[name]!r}" if name in current else ""
        print(f"  {name} ({ftype.__name__}, {fflags.describe_allowed(name)}) — {desc}{marker}{value}")
    return 0


def cmd_fflags_get(args: argparse.Namespace) -> int:
    flags = fflags.current_fflags()
    if args.name in flags:
        print(json.dumps(flags[args.name]))
        return 0
    print(f"Flag {args.name!r} não está definida.", file=sys.stderr)
    return 1


def cmd_fflags_set(args: argparse.Namespace) -> int:
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value
    try:
        flags = fflags.set_flag(args.name, value, force=args.force)
    except (fflags.FFFlagError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"OK: fflags[{args.name!r}] = {flags[args.name]!r}")
    return 0


def cmd_fflags_unset(args: argparse.Namespace) -> int:
    flags = fflags.remove_flag(args.name)
    if args.name in flags:
        print(f"Erro: não foi possível remover {args.name!r}", file=sys.stderr)
        return 1
    print(f"OK: {args.name!r} removida (se existia).")
    return 0


def cmd_fflags_preset(args: argparse.Namespace) -> int:
    try:
        flags = fflags.apply_preset(args.preset)
    except (fflags.FFFlagError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Preset {args.preset!r} aplicado. Flags ativas: {len(flags)}")
    desc = constants.PRESET_DESCRIPTIONS.get(args.preset)
    if desc:
        print(desc)
    return 0


# ---------------------------------------------------------------- mods
def cmd_mods_list(args: argparse.Namespace) -> int:
    installed = mods.list_mods()
    if not installed:
        print("Nenhum mod instalado no asset_overlay.")
        return 0
    for m in installed:
        print(f"{m.size:>10}  {m.rel_path}")
    return 0


def cmd_mods_install(args: argparse.Namespace) -> int:
    try:
        installed = mods.install_zip(Path(args.zip), overwrite=not args.no_overwrite)
    except mods.ModError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Instalado {len(installed)} arquivo(s):")
    for rel in installed:
        print(f"  {rel}")
    return 0


def cmd_mods_remove(args: argparse.Namespace) -> int:
    try:
        removed = mods.remove_path(args.path)
    except mods.ModError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print("Removido." if removed else "Caminho não encontrado no overlay.")
    return 0 if removed else 1


def cmd_mods_clear(args: argparse.Namespace) -> int:
    if not args.yes:
        reply = input("Remover TODOS os mods do asset_overlay? [y/N] ")
        if reply.strip().lower() not in ("y", "yes", "s", "sim"):
            print("Cancelado.")
            return 0
    count = mods.clear_all()
    print(f"{count} arquivo(s) removido(s).")
    return 0


# ---------------------------------------------------------------- backups
def cmd_backup_create(args: argparse.Namespace) -> int:
    try:
        info = backups.create_backup(label=args.label)
    except FileNotFoundError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Backup criado: {info.path}")
    return 0


def cmd_backup_list(args: argparse.Namespace) -> int:
    infos = backups.list_backups()
    if not infos:
        print("Nenhum backup.")
        return 0
    for info in infos:
        size = info.path.stat().st_size
        print(f"{info.stamp}  {size:>8} bytes  {info.path.name}")
    return 0


def cmd_backup_restore(args: argparse.Namespace) -> int:
    try:
        cfg = backups.restore_backup(Path(args.backup))
    except FileNotFoundError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Restaurado para {cfg}")
    return 0


# ---------------------------------------------------------------- play (modo simples)
def cmd_play(args: argparse.Namespace) -> int:
    """Modo simples: aplica o perfil de flags escolhido e joga.

    É aqui que o Blunix agrega valor: o perfil entra em vigor no momento em
    que você joga. Abrir o Sober direto continua funcionando normalmente.
    """
    # aliases em inglês (docs/repo são English-first)
    _ALIASES = {"light": "leve", "medium": "medio", "full": "completo",
                "default": "default", "padrao": "default"}
    profile = args.profile
    if profile is None:
        profile = settings.load().get("profile", "medio")
    else:
        profile = _ALIASES.get(profile, profile)
        settings.save({"profile": profile})  # lembra a escolha

    if profile != "off":
        try:
            flags = fflags.stage_preset(profile)
            config.write_config({"fflags": flags})
            print(f"Perfil '{profile}' aplicado ({len(flags)} flags).")
        except (fflags.FFFlagError, ValueError) as exc:
            print(f"Erro no perfil: {exc}", file=sys.stderr)
            return 1
    else:
        print("Sem flags (perfil 'off').")

    place = args.place
    try:
        if launcher.is_running() and not args.new and place is None:
            print("Roblox já está aberto — reinicie-o para valer o novo perfil!")
            return 0
        result = launcher.launch(place, wait=args.wait)
    except launcher.LaunchError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        print("Dica: use o número do jogo, ex.: blunix play 2753915549", file=sys.stderr)
        return 1
    if isinstance(result, int):
        return 0 if result == 0 else 1
    print("Abrindo o Roblox… divirta-se! 🎮")
    return 0


# ---------------------------------------------------------------- menu do sistema
def cmd_install_menu(_args: argparse.Namespace) -> int:
    try:
        result = desktop_integration.install_menu()
    except OSError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Atalho criado no menu de aplicativos: {result.desktop_path}")
    if result.icon_path:
        print(f"Ícone instalado: {result.icon_path}")
    print(f"Comando: {result.exec_line}")
    return 0


def cmd_uninstall_menu(_args: argparse.Namespace) -> int:
    removed = desktop_integration.uninstall_menu()
    print("Atalho removido do menu." if removed else "Não havia atalho instalado.")
    return 0


# ---------------------------------------------------------------- launch
def cmd_launch(args: argparse.Namespace) -> int:
    if launcher.is_running() and not args.new:
        print("Sober já está rodando (use --new para abrir outra instância).")
        return 0
    try:
        result = launcher.launch(args.place, wait=args.wait)  # launch já extrai placeId de links
    except launcher.LaunchError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    if isinstance(result, int):
        return 0 if result == 0 else 1
    print("Sober lançado.")
    return 0


# ---------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blunix",
        description=f"{constants.APP_NAME} — gerenciador do Sober (Roblox no Linux)",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {constants.VERSION}")
    parser.add_argument("-v", "--verbose", action="store_true", help="logging detalhado")
    parser.add_argument("--logfile", action="store_true", help="grava log em ~/.local/state/blunix/")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gui", help="abre a interface gráfica (GTK4)")
    p.set_defaults(func=cmd_gui)

    p = sub.add_parser("doctor", help="verifica o ambiente (CPU, flatpak, Sober, Vulkan)")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("play", help="JOGAR — aplica o perfil escolhido e abre o Roblox")
    p.add_argument("place", nargs="?", default=None,
                   help="número do jogo (placeId), link roblox:// ou URL do site")
    p.add_argument("--profile", default=None,
                   choices=["leve", "medio", "completo", "padrao", "off",
                            "light", "medium", "full", "default"],
                   help="flag profile (default: last used, initially 'medium'; "
                        "pt aliases: leve/medio/completo/padrao)")
    p.add_argument("--wait", action="store_true", help="espera o processo terminar")
    p.add_argument("--new", action="store_true", help="abre mesmo se já houver Roblox rodando")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("install-menu", help="cria atalho no menu de aplicativos (ícone)")
    p.set_defaults(func=cmd_install_menu)

    p = sub.add_parser("uninstall-menu", help="remove o atalho do menu")
    p.set_defaults(func=cmd_uninstall_menu)

    p = sub.add_parser("launch", help="abre o Roblox (Sober)")
    p.add_argument("--place", metavar="PLACE_ID", help="abre uma experience pelo placeId")
    p.add_argument("--wait", action="store_true", help="espera o processo terminar")
    p.add_argument("--new", action="store_true", help="lança mesmo se já houver Sober rodando")
    p.set_defaults(func=cmd_launch)

    p = sub.add_parser("config", help="configurações gerais do Sober")
    csub = p.add_subparsers(dest="subcommand", required=True)
    p2 = csub.add_parser("show", help="mostra a config atual")
    p2.add_argument("--json", action="store_true")
    p2.set_defaults(func=cmd_config_show)
    p2 = csub.add_parser("set", help="define uma chave (ex.: config set close_on_leave true)")
    p2.add_argument("key")
    p2.add_argument("value")
    p2.set_defaults(func=cmd_config_set)
    p2 = csub.add_parser("reset", help="restaura os defaults do schema")
    p2.set_defaults(func=cmd_config_reset)

    p = sub.add_parser("fflags", help="FastFlags (allowlist pós-2025-09-30)")
    fsub = p.add_subparsers(dest="subcommand", required=True)
    p2 = fsub.add_parser("list", help="lista allowlist e flags ativas")
    p2.add_argument("--json", action="store_true")
    p2.set_defaults(func=cmd_fflags_list)
    p2 = fsub.add_parser("get", help="mostra o valor de uma flag ativa")
    p2.add_argument("name")
    p2.set_defaults(func=cmd_fflags_get)
    p2 = fsub.add_parser("set", help="define uma flag (validada contra a allowlist)")
    p2.add_argument("name")
    p2.add_argument("value")
    p2.add_argument("--force", action="store_true", help="escreve mesmo fora da allowlist")
    p2.set_defaults(func=cmd_fflags_set)
    p2 = fsub.add_parser("unset", help="remove uma flag")
    p2.add_argument("name")
    p2.set_defaults(func=cmd_fflags_unset)
    p2 = fsub.add_parser("preset", help="aplica um preset (leve | medio | completo | default)")
    p2.add_argument("preset", choices=sorted(constants.FFLAG_PRESETS))
    p2.set_defaults(func=cmd_fflags_preset)

    p = sub.add_parser("mods", help="mods via asset_overlay")
    msub = p.add_subparsers(dest="subcommand", required=True)
    p2 = msub.add_parser("list", help="lista arquivos no overlay")
    p2.set_defaults(func=cmd_mods_list)
    p2 = msub.add_parser("install", help="instala um mod .zip")
    p2.add_argument("zip")
    p2.add_argument("--no-overwrite", action="store_true")
    p2.set_defaults(func=cmd_mods_install)
    p2 = msub.add_parser("remove", help="remove um arquivo ou pasta do overlay")
    p2.add_argument("path")
    p2.set_defaults(func=cmd_mods_remove)
    p2 = msub.add_parser("clear", help="remove todos os mods")
    p2.add_argument("-y", "--yes", action="store_true")
    p2.set_defaults(func=cmd_mods_clear)

    p = sub.add_parser("backup", help="backups do config.json")
    bsub = p.add_subparsers(dest="subcommand", required=True)
    p2 = bsub.add_parser("create", help="cria um backup")
    p2.add_argument("--label", default=None)
    p2.set_defaults(func=cmd_backup_create)
    p2 = bsub.add_parser("list", help="lista backups")
    p2.set_defaults(func=cmd_backup_list)
    p2 = bsub.add_parser("restore", help="restaura um backup (nome ou caminho)")
    p2.add_argument("backup")
    p2.set_defaults(func=cmd_backup_restore)

    return parser


def cmd_gui(_args: argparse.Namespace) -> int:
    try:
        from .gui import run
    except ImportError as exc:
        print(f"GTK 4 / PyGObject não disponível: {exc}", file=sys.stderr)
        return 2
    return run()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose, args.logfile)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
