"""Internacionalização simples (pt/en).

- Idioma salvo em settings.json ("language": "auto" | "pt" | "en").
- "auto" detecta pelo ambiente (LANG/LC_ALL): começando com "pt" -> pt, senão en.
- t("chave") retorna o texto no idioma ativo; chaves ausentes caem para pt.
"""
from __future__ import annotations

import os

from . import settings

STRINGS: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------------- pt
    "pt": {
        # menu principal
        "menu.play": "🎮  JOGAR",
        "menu.play_sub": "abre o Roblox com seu perfil",
        "menu.conf": "⚙  Configuração",
        "menu.conf_sub": "gráficos, flags, mods e sistema",
        "menu.falta": "⚠ Falta: {items}",
        # abas / janelas
        "tab.system": "Sistema",
        "tab.config": "Config",
        "tab.fflags": "FastFlags",
        "tab.mods": "Mods",
        "tab.backups": "Backups",
        "win.settings": "Blunix — Configuração",
        "win.minimize": "Minimizar",
        "win.close": "Fechar",
        # sistema
        "sys.profile_title": "Perfil de qualidade (usado pelo botão JOGAR)",
        "sys.apply_now": "Aplicar agora",
        "sys.diag": "Diagnóstico do sistema",
        "sys.refresh": "Verificar de novo",
        "sys.link_ph": "nº do jogo ou link (ex.: 2753915549)",
        "sys.open_game": "Abrir jogo",
        "sys.profile_applied": "Perfil '{name}' aplicado",
        "sys.restart_roblox": "Reinicie o Roblox para valer.",
        # presets (descrições)
        "desc.leve": "Muda pouco: anti-aliasing desligado e texturas um pouco mais leves; grama visível só até 400 studs. Visual quase igual, FPS um pouco melhor.",
        "desc.medio": "Equilibrado: texturas leves, sombreamento reduzido, detalhes de CSG simplificados e grama curta. Bom ganho de FPS mantendo o jogo bonito.",
        "desc.completo": "Muda muito: foco total em FPS — iluminação simples, céu cinza, texturas mínimas, grama removida e LOD agressivo. Visual bem diferente.",
        "desc.default": "Limpa todas as flags de preset e volta ao comportamento padrão do Sober.",
        # fflags
        "ff.warn": "⚠ A Roblox só aceita uma lista fixa de flags (desde 30/09/2025). Tudo aqui está dentro dessa lista. Reinicie o Roblox depois de mudar.",
        "ff.active": "Flags ativas (o que cada uma faz)",
        "ff.adv": "Avançado: definir flag manualmente",
        "ff.value_ph": "valor (true/false ou número)",
        "ff.set": "Definir",
        "ff.remove_selected": "Remover flag selecionada",
        "ff.empty": "(nenhuma flag definida — comportamento padrão do Sober)",
        "ff.not_allowed": "(fora da allowlist — não tem efeito)",
        "ff.recommended": "Recomendado — escolha o quanto quer mudar no visual:",
        "ff.level_leve": "Leve",
        "ff.level_medio": "Médio",
        "ff.level_completo": "Completo",
        "ff.sub_leve": "muda pouco",
        "ff.sub_medio": "equilibrado",
        "ff.sub_completo": "muda muito",
        "ff.reset_presets": "Voltar ao padrão (limpar flags de preset)",
        "ff.q_apply": "Aplicar preset {name}?",
        "ff.q_apply_detail": "{desc}\n\nIsso substitui as flags dos outros presets; flags que você definiu manualmente são mantidas.",
        "ff.q_reset": "Limpar flags de preset?",
        "ff.q_reset_detail": "Volta ao comportamento padrão do Sober. Flags definidas manualmente são mantidas.",
        # config
        "cfg.hint": "Opções oficiais do Sober. Reinicie o Roblox após salvar.",
        "cfg.save": "Salvar configuração",
        "cfg.saved": "Configuração salva",
        # mods
        "mods.hint": "Mods vão para o asset_overlay do Sober, espelhando a estrutura do base.apk (ex.: content/textures/Cursors/...). Reinicie o Roblox para aplicar.",
        "mods.install": "Instalar mod (.zip)…",
        "mods.remove": "Remover selecionado",
        "mods.clear": "Limpar tudo",
        "mods.empty": "(nenhum mod instalado)",
        "mods.q_clear": "Limpar todos os mods?",
        "mods.q_clear_detail": "Todos os arquivos do asset_overlay serão removidos.",
        "mods.installed": "Mod instalado ({n} arquivo(s))",
        "mods.err_install": "Erro ao instalar mod",
        "mods.err_remove": "Erro ao remover",
        # backups
        "bk.hint": "Backups do config.json em {path}. Nunca incluem cookies/sessão.",
        "bk.create": "Criar backup",
        "bk.restore": "Restaurar selecionado",
        "bk.empty": "(nenhum backup)",
        "bk.q_restore": "Restaurar backup?",
        "bk.q_restore_detail": "O config.json atual será substituído por {name}",
        "bk.created": "Backup criado",
        "bk.restored": "Backup restaurado",
        # idioma
        "lang.label": "Idioma / Language",
        "lang.auto": "Automático",
        "lang.restart": "Reinicie o Blunix para trocar o idioma.",
        "lang.saved": "Idioma salvo",
        # diálogos comuns
        "dlg.ok": "OK",
        "dlg.yes": "Sim",
        "dlg.no": "Não",
        "dlg.err_play": "Não dá para abrir ainda",
        "dlg.err_play_detail": "Resolva primeiro: {items}",
        "dlg.err_launch": "Erro ao abrir o Roblox",
        "dlg.err_profile": "Erro ao aplicar o perfil",
        "dlg.err_save": "Erro ao salvar",
        "dlg.err_restore": "Erro",
        # status
        "env.ok": "Tudo pronto! ✅",
        "env.falta": "Ops… falta alguma coisa ⚠",
        # diagnóstico (nomes das checagens e detalhes)
        "chk.arch": "Arquitetura",
        "chk.arch.arm": " (Sober oficial é x86_64; ARM é beta)",
        "chk.sse": "CPU SSE4.1/4.2",
        "chk.sse.ok": "presentes",
        "chk.sse.fail": "AUSENTES — o Sober não vai rodar",
        "chk.flatpak": "Flatpak",
        "chk.flatpak.ok": "instalado",
        "chk.flatpak.fail": "não encontrado no PATH",
        "chk.sober": "Sober",
        "chk.sober.ok": "instalado (versão {ver})",
        "chk.sober.ok_nover": "instalado",
        "chk.sober.fail": "não instalado — 'flatpak install flathub {app_id}'",
        "chk.sober.unknown": "impossível verificar sem flatpak",
        "chk.vulkan": "Vulkan",
        "chk.vulkan.ok": "disponível",
        "chk.vulkan.warn_fail": "presente mas falhou (Sober cai p/ OpenGL)",
        "chk.vulkan.warn_missing": "vulkaninfo não instalado — não dá para verificar (Sober usa OpenGL como fallback)",
        "chk.cfg": "Config do Sober",
        "chk.cfg.ok": "existente",
        "chk.cfg.warn": "ainda não existe (criada no 1º boot do Sober)",
    },
    # ---------------------------------------------------------------- en
    "en": {
        "menu.play": "🎮  PLAY",
        "menu.play_sub": "opens Roblox with your profile",
        "menu.conf": "⚙  Settings",
        "menu.conf_sub": "graphics, flags, mods and system",
        "menu.falta": "⚠ Missing: {items}",
        "tab.system": "System",
        "tab.config": "Config",
        "tab.fflags": "FastFlags",
        "tab.mods": "Mods",
        "tab.backups": "Backups",
        "win.settings": "Blunix — Settings",
        "win.minimize": "Minimize",
        "win.close": "Close",
        "sys.profile_title": "Quality profile (used by the PLAY button)",
        "sys.apply_now": "Apply now",
        "sys.diag": "System check",
        "sys.refresh": "Check again",
        "sys.link_ph": "game number or link (e.g.: 2753915549)",
        "sys.open_game": "Open game",
        "sys.profile_applied": "Profile '{name}' applied",
        "sys.restart_roblox": "Restart Roblox to apply.",
        "desc.leve": "Small change: anti-aliasing off and slightly lighter textures; grass visible up to 400 studs. Looks almost the same, a bit more FPS.",
        "desc.medio": "Balanced: light textures, reduced shading, simplified CSG detail and short grass. Good FPS gain while keeping the game pretty.",
        "desc.completo": "Big change: full FPS focus — simple lighting, gray sky, minimal textures, grass removed and aggressive LOD. Looks very different.",
        "desc.default": "Clears all preset flags and returns to Sober's default behavior.",
        "ff.warn": "⚠ Roblox only accepts a fixed flag allowlist (since 09/30/2025). Everything here is within that list. Restart Roblox after changing.",
        "ff.active": "Active flags (what each one does)",
        "ff.adv": "Advanced: set a flag manually",
        "ff.value_ph": "value (true/false or number)",
        "ff.set": "Set",
        "ff.remove_selected": "Remove selected flag",
        "ff.empty": "(no flags set — Sober default behavior)",
        "ff.not_allowed": "(outside the allowlist — no effect)",
        "ff.recommended": "Recommended — pick how much you want to change:",
        "ff.level_leve": "Light",
        "ff.level_medio": "Medium",
        "ff.level_completo": "Full",
        "ff.sub_leve": "small change",
        "ff.sub_medio": "balanced",
        "ff.sub_completo": "big change",
        "ff.reset_presets": "Back to default (clear preset flags)",
        "ff.q_apply": "Apply {name} preset?",
        "ff.q_apply_detail": "{desc}\n\nThis replaces flags from other presets; manually set flags are kept.",
        "ff.q_reset": "Clear preset flags?",
        "ff.q_reset_detail": "Returns to Sober's default behavior. Manually set flags are kept.",
        "cfg.hint": "Official Sober options. Restart Roblox after saving.",
        "cfg.save": "Save configuration",
        "cfg.saved": "Configuration saved",
        "mods.hint": "Mods go into Sober's asset_overlay, mirroring the base.apk structure (e.g.: content/textures/Cursors/...). Restart Roblox to apply.",
        "mods.install": "Install mod (.zip)…",
        "mods.remove": "Remove selected",
        "mods.clear": "Clear all",
        "mods.empty": "(no mods installed)",
        "mods.q_clear": "Clear all mods?",
        "mods.q_clear_detail": "Every file in asset_overlay will be removed.",
        "mods.installed": "Mod installed ({n} file(s))",
        "mods.err_install": "Error installing mod",
        "mods.err_remove": "Error removing",
        "bk.hint": "Backups of config.json at {path}. Never include cookies/session.",
        "bk.create": "Create backup",
        "bk.restore": "Restore selected",
        "bk.empty": "(no backups)",
        "bk.q_restore": "Restore backup?",
        "bk.q_restore_detail": "Current config.json will be replaced by {name}",
        "bk.created": "Backup created",
        "bk.restored": "Backup restored",
        "lang.label": "Idioma / Language",
        "lang.auto": "Automatic",
        "lang.restart": "Restart Blunix to switch the language.",
        "lang.saved": "Language saved",
        "dlg.ok": "OK",
        "dlg.yes": "Yes",
        "dlg.no": "No",
        "dlg.err_play": "Can't open yet",
        "dlg.err_play_detail": "Fix first: {items}",
        "dlg.err_launch": "Error launching Roblox",
        "dlg.err_profile": "Error applying profile",
        "dlg.err_save": "Error saving",
        "dlg.err_restore": "Error",
        "env.ok": "All set! ✅",
        "env.falta": "Oops… something is missing ⚠",
        "chk.arch": "Architecture",
        "chk.arch.arm": " (official Sober is x86_64; ARM is beta)",
        "chk.sse": "CPU SSE4.1/4.2",
        "chk.sse.ok": "present",
        "chk.sse.fail": "MISSING — Sober will not run",
        "chk.flatpak": "Flatpak",
        "chk.flatpak.ok": "installed",
        "chk.flatpak.fail": "not found in PATH",
        "chk.sober": "Sober",
        "chk.sober.ok": "installed (version {ver})",
        "chk.sober.ok_nover": "installed",
        "chk.sober.fail": "not installed — 'flatpak install flathub {app_id}'",
        "chk.sober.unknown": "can't check without flatpak",
        "chk.vulkan": "Vulkan",
        "chk.vulkan.ok": "available",
        "chk.vulkan.warn_fail": "present but failed (Sober falls back to OpenGL)",
        "chk.vulkan.warn_missing": "vulkaninfo not installed — can't check (Sober uses OpenGL as fallback)",
        "chk.cfg": "Sober config",
        "chk.cfg.ok": "exists",
        "chk.cfg.warn": "doesn't exist yet (created on Sober's first boot)",
    },
}

# Resolvido uma vez por processo (simples e suficiente para o app)
_LANG: str | None = None


def _detect_lang() -> str:
    saved = settings.load().get("language", "auto")
    if saved in ("pt", "en"):
        return saved
    env = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES")
           or os.environ.get("LANG") or "en")
    return "pt" if env.lower().startswith("pt") else "en"


def lang() -> str:
    global _LANG
    if _LANG is None:
        _LANG = _detect_lang()
    return _LANG


def t(key: str, **fmt) -> str:
    """Texto no idioma ativo; cai para pt e depois para a própria chave."""
    text = STRINGS.get(lang(), {}).get(key) or STRINGS["pt"].get(key) or key
    return text.format(**fmt) if fmt else text
