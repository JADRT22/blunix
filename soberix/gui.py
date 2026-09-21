"""GUI GTK4 do Soberix: menu compacto + janela de configuração (Sistema, Config,
FastFlags, Mods, Backups). Textos em PT/EN via i18n.

Importada apenas quando a GUI é solicitada, para o CLI funcionar sem GTK.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk, Pango  # noqa: E402

from . import activity, backups, config, constants, desktop_integration, environment, fflags, history, launcher, mods, settings, updates  # noqa: E402
from . import shortcut_refresh  # noqa: E402
from .i18n import t, set_lang  # noqa: E402
from . import i18n  # noqa: E402


def _message_dialog(
    parent: Gtk.Window,
    title: str,
    detail: str,
    buttons: list[tuple[str, int]],
    icon: str = "dialog-information",
) -> Gtk.Dialog:
    """Diálogo próprio com Gtk.Dialog (o Gtk.MessageDialog foi removido no GTK4 novo)."""
    dlg = Gtk.Dialog(transient_for=parent, modal=True, use_header_bar=True)
    dlg.set_title("")
    header = dlg.get_header_bar()
    if header is not None:
        header.set_title_widget(Gtk.Label())  # sem título duplicado
    for label, response in buttons:
        dlg.add_button(label, response)
    dlg.set_default_response(buttons[-1][1])

    content = dlg.get_content_area()
    content.set_spacing(10)
    content.set_margin_top(18)
    content.set_margin_bottom(6)
    content.set_margin_start(18)
    content.set_margin_end(18)

    icon_lbl = Gtk.Label()
    icon_lbl.set_markup(f"<span size='xx-large'>{icon}</span>")
    icon_lbl.set_halign(Gtk.Align.CENTER)
    content.append(icon_lbl)

    title_lbl = Gtk.Label()
    title_lbl.set_markup(f"<b><big>{GLib.markup_escape_text(title)}</big></b>")
    title_lbl.set_halign(Gtk.Align.CENTER)
    title_lbl.set_wrap(True)
    content.append(title_lbl)

    if detail:
        detail_lbl = Gtk.Label(label=detail)
        detail_lbl.set_halign(Gtk.Align.CENTER)
        detail_lbl.set_wrap(True)
        detail_lbl.set_max_width_chars(48)
        detail_lbl.add_css_class("dim-label")
        content.append(detail_lbl)
    return dlg


def _toast(parent: Gtk.Window, title: str, detail: str = "", error: bool = False) -> None:
    dlg = _message_dialog(
        parent, title, detail,
        buttons=[(t("dlg.ok"), Gtk.ResponseType.OK)],
        icon="dialog-error" if error else "dialog-information",
    )
    dlg.connect("response", lambda d, _r: d.destroy())
    dlg.present()


def _ui_scale() -> float:
    """Fator de escala da UI com base na resolução do monitor.

    - Base: 1920px físicos = 1.0×. 1440p ≈ 1.33×, 4K ≈ 2.0×.
    - Geometria do monitor é em pixels LÓGICOS (já dividida pelo scale/
      zoom do desktop), então multiplicamos de volta pelo scale factor —
      assim zoom 150%/200% em telas HiDPI não deixa o menu pequeno.
    - Limitado a [1.0, 2.0]: nunca menor que o layout original.
    """
    try:
        display = Gdk.Display.get_default()
        mon = display.get_monitor(0)
        geom = mon.get_geometry()
        scale = max(mon.get_scale_factor(), 1)
        physical_w = max(geom.width, 1) * scale
        return max(1.0, min(physical_w / 1920.0, 2.0))
    except Exception:  # noqa: BLE001 — qualquer erro: escala 1.0
        return 1.0


def _confirm(parent: Gtk.Window, title: str, detail: str) -> bool:
    result: list[bool] = []

    def on_answer(dlg: Gtk.Dialog, response: int) -> None:
        result.append(response == Gtk.ResponseType.YES)
        dlg.destroy()

    dlg = _message_dialog(
        parent, title, detail,
        buttons=[(t("dlg.no"), Gtk.ResponseType.NO), (t("dlg.yes"), Gtk.ResponseType.YES)],
        icon="dialog-question",
    )
    dlg.connect("response", on_answer)
    dlg.present()
    while not result:
        GLib.main_context_default().iteration(True)
    return result[0]


class SoberixWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(constants.APP_NAME)
        self._s = _ui_scale()  # fator de escala (resolução/zoom do monitor)
        self.set_default_size(round(400 * self._s), round(210 * self._s))
        self._setup_css()

        header = Gtk.HeaderBar()
        header.set_show_title_buttons(False)  # sem maximizar/tela cheia
        title_lbl = Gtk.Label()
        title_lbl.set_markup(f"<b>{constants.APP_NAME}</b>")
        header.set_title_widget(title_lbl)

        # botões manuais: só minimizar e fechar
        btn_min = Gtk.Button.new_from_icon_name("window-minimize-symbolic")
        btn_min.add_css_class("flat")
        btn_min.set_tooltip_text(t("win.minimize"))
        btn_min.connect("clicked", lambda *_a: self.minimize())
        btn_close = Gtk.Button.new_from_icon_name("window-close-symbolic")
        btn_close.add_css_class("flat")
        btn_close.set_tooltip_text(t("win.close"))
        btn_close.connect("clicked", lambda *_a: self._on_main_close())
        header.pack_end(btn_close)
        header.pack_end(btn_min)
        self.set_titlebar(header)

        self.set_resizable(False)  # menu com tamanho fixo (impossível maximizar)
        self.set_icon_name(desktop_integration.DESKTOP_ID)  # ícone no taskbar
        self.connect("notify::maximized", self._block_maximize)

        self._lang_switching = False
        self.set_child(self._build_menu_page())
        self._build_settings_window()
        self.connect("close-request", self._on_main_close)
        # tela cheia bloqueada: só minimizar/maximizar/fechar
        self.connect("notify::fullscreened", self._block_fullscreen)

    # ------------------------------------------------------------ janela de configuração
    def _build_settings_window(self) -> None:
        """Configuração abre em uma janela separada (o menu permanece pequeno)."""
        self.settings_win = Gtk.ApplicationWindow(application=self.get_application())
        self.settings_win.set_title(t("win.settings"))
        self.settings_win.set_default_size(round(860 * self._s), round(620 * self._s))
        self.settings_win.set_icon_name(desktop_integration.DESKTOP_ID)
        # sem maximizar/tela cheia: só minimizar e fechar (redimensionar livre)
        hdr = Gtk.HeaderBar()
        hdr.set_show_title_buttons(False)
        smin = Gtk.Button.new_from_icon_name("window-minimize-symbolic")
        smin.add_css_class("flat")
        smin.connect("clicked", lambda *_a: self.settings_win.minimize())
        sclose = Gtk.Button.new_from_icon_name("window-close-symbolic")
        sclose.add_css_class("flat")
        sclose.connect("clicked", lambda *_a: self.settings_win.hide())
        hdr.pack_end(sclose)
        hdr.pack_end(smin)
        self.settings_win.set_titlebar(hdr)
        self.settings_win.connect("notify::maximized", self._block_maximize)
        # fechar a janela de configuração só a esconde (o menu segue aberto)
        self.settings_win.connect("close-request", self._on_settings_close)

        self.inner_stack = Gtk.Stack()
        self.inner_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        inner_switcher = Gtk.StackSwitcher()
        inner_switcher.set_stack(self.inner_stack)
        inner_switcher.set_halign(Gtk.Align.CENTER)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        page.append(inner_switcher)
        page.append(self.inner_stack)
        self.settings_win.set_child(page)
        self.settings_win.connect("notify::fullscreened", self._block_fullscreen)

        self.inner_stack.add_titled(self._build_system_tab(), "system", t("tab.system"))
        self.inner_stack.add_titled(self._build_config_tab(), "config", t("tab.config"))
        self.inner_stack.add_titled(self._build_fflags_tab(), "fflags", t("tab.fflags"))
        self.inner_stack.add_titled(self._build_servers_card(), "servers", t("tab.servers"))
        self.inner_stack.add_titled(self._build_mods_tab(), "mods", t("tab.mods"))
        self.inner_stack.add_titled(self._build_backups_tab(), "backups", t("tab.backups"))

    def _open_settings(self) -> None:
        self.settings_win.present()

    def _on_settings_close(self, *_a) -> bool:
        self.settings_win.hide()
        return True

    def _block_fullscreen(self, window: Gtk.Window, _pspec) -> None:
        """Desfaz qualquer tentativa de tela cheia (F11, atalho do compositor)."""
        if window.is_fullscreen():
            window.unfullscreen()

    def _block_maximize(self, window: Gtk.Window, _pspec) -> None:
        """Menu nunca fica maximizado (janela compacta por design)."""
        if window.is_maximized():
            window.unmaximize()

    def _on_main_close(self, *_a) -> bool:
        """Fechar o menu encerra o app (nada fica rodando em background)."""
        watcher = getattr(self, "_activity_watcher", None)
        if watcher is not None:
            watcher.stop()
        if getattr(self, "settings_win", None) is not None:
            self.settings_win.destroy()
        self.destroy()
        return True

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _scrolled(child: Gtk.Widget) -> Gtk.ScrolledWindow:
        sc = Gtk.ScrolledWindow()
        sc.set_child(child)
        sc.set_vexpand(True)
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        return sc

    @staticmethod
    def _setup_css() -> None:
        """Fundo preto fosco + botões do menu (azul-escuro e cinza).

        Fonte do texto dim escala com a resolução (o GTK interpola px)."""
        s = _ui_scale()
        dim_px = round(11 * s)
        css = f"""
.soberix-menu {{ background-color: #101013; }}
.soberix-menu .play-btn {{ background-color: #0A3D7A; color: #ffffff; }}
.soberix-menu .play-btn:hover {{ background-color: #0C4A94; }}
.soberix-menu .play-btn:active {{ background-color: #08335F; }}
.soberix-menu .conf-btn {{ background-color: #26262B; color: #DDDDDD; }}
.soberix-menu .conf-btn:hover {{ background-color: #323238; }}
.soberix-menu .dim {{ color: #8f8f98; font-size: {dim_px}px; }}
.game-chip {{ padding: 2px 10px; border-radius: 9999px; }}
""".encode()
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ------------------------------------------------------------ Início (modo simples)
    PROFILE_LABELS = (("leve", "ff.level_leve"), ("medio", "ff.level_medio"), ("completo", "ff.level_completo"), ("default", "ff.level_default"))

    def _build_menu_page(self) -> Gtk.Widget:
        """Menu compacto: logo à esquerda; JOGAR (azul-escuro) em cima,
        Configuração (cinza) embaixo. Fundo preto fosco."""
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class("soberix-menu")

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16,
                        margin_top=18, margin_bottom=18, margin_start=18, margin_end=18,
                        halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        root.append(outer)

        # logo à esquerda (procura no projeto, no pacote e dentro do AppImage)
        icon_path = desktop_integration.find_icon()
        if icon_path is not None:
            img = Gtk.Image.new_from_file(str(icon_path))
            img.set_pixel_size(round(76 * self._s))
            img.set_valign(Gtk.Align.CENTER)
            img.set_halign(Gtk.Align.CENTER)
            outer.append(img)

        # coluna de botões
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                      valign=Gtk.Align.CENTER, hexpand=True)
        outer.append(col)

        self.btn_big_play = Gtk.Button()
        self.btn_big_play.add_css_class("play-btn")
        play_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1,
                               margin_top=10, margin_bottom=10, margin_start=22, margin_end=22)
        p1 = Gtk.Label()
        p1.set_markup(f"<b>{t('menu.play')}</b>")
        p2 = Gtk.Label(label=t("menu.play_sub"))
        p2.add_css_class("dim")
        play_content.append(p1)
        play_content.append(p2)
        self.btn_big_play.set_child(play_content)
        self.btn_big_play.connect("clicked", self._on_big_play)
        self.btn_big_play.set_size_request(round(232 * self._s), -1)  # largura igual p/ alinhar
        col.append(self.btn_big_play)

        # chips de jogos (favoritos + recentes) — 1 clique para jogar de novo
        self.games_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._refresh_games_row()
        col.append(self.games_row)

        # "jogando agora" / último servidor (activity tracking via logs do Sober)
        self.activity_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.activity_row.set_margin_top(4)
        col.append(self.activity_row)
        self._current_activity = None
        self._refresh_activity_row()
        self._start_activity_watcher()

        btn_conf = Gtk.Button()
        btn_conf.add_css_class("conf-btn")
        conf_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1,
                               margin_top=8, margin_bottom=8, margin_start=22, margin_end=22)
        c1 = Gtk.Label()
        c1.set_markup(f"<b>{t('menu.conf')}</b>")
        c2 = Gtk.Label(label=t("menu.conf_sub"))
        c2.add_css_class("dim")
        conf_content.append(c1)
        conf_content.append(c2)
        btn_conf.set_child(conf_content)
        btn_conf.connect("clicked", lambda _b: self._open_settings())
        btn_conf.set_size_request(round(232 * self._s), -1)  # largura igual p/ alinhar
        col.append(btn_conf)

        # status compacto (uma linha) + banner de atualização
        self.home_status = Gtk.Label()
        self.home_status.set_justify(Gtk.Justification.CENTER)
        self.home_status.set_wrap(True)
        self.home_status.add_css_class("dim")
        root.append(self.home_status)

        # banner de atualização (aparece só quando há versão nova)
        self.upd_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10,
                                  margin_top=6, margin_bottom=10,
                                  margin_start=12, margin_end=12,
                                  halign=Gtk.Align.CENTER)
        self.upd_label = Gtk.Label()
        self.upd_label.add_css_class("dim")
        btn_upd = Gtk.Button(label=t("upd.download"))
        btn_upd.add_css_class("suggested-action")
        btn_upd.connect("clicked", self._on_open_release)
        self.upd_banner.append(self.upd_label)
        self.upd_banner.append(btn_upd)
        self.upd_banner.set_visible(False)
        root.append(self.upd_banner)

        self._refresh_checks()
        self._update_home_status()
        self._check_updates_async()
        return root

    def _build_system_tab(self) -> Gtk.Widget:
        """Aba Sistema: perfil padrão, link para abrir jogo e diagnóstico."""
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                        margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        # ---- perfil padrão (aplicado ao clicar em JOGAR no menu)
        prof_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                            margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        prof_card.add_css_class("card")
        t_lbl = Gtk.Label()
        t_lbl.set_markup(f"<b>{t('sys.profile_title')}</b>")
        t_lbl.set_halign(Gtk.Align.START)
        prof_card.append(t_lbl)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.profile_dd = Gtk.DropDown(model=Gtk.StringList.new([t(k) for _lbl, k in self.PROFILE_LABELS]))
        saved = settings.load().get("profile", "medio")
        keys = [k for _lbl, k in self.PROFILE_LABELS]
        if saved in keys:
            self.profile_dd.set_selected(keys.index(saved))
        btn_apply = Gtk.Button(label=t("sys.apply_now"))
        btn_apply.add_css_class("suggested-action")
        btn_apply.connect("clicked", self._on_apply_profile_now)
        row.append(self.profile_dd)
        row.append(btn_apply)
        row.set_halign(Gtk.Align.START)
        prof_card.append(row)

        desc = Gtk.Label()
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        self.profile_desc = desc
        self.profile_dd.connect("notify::selected", self._on_profile_desc)
        self._on_profile_desc()
        prof_card.append(desc)

        link_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.link_entry = Gtk.Entry()
        self.link_entry.set_hexpand(True)
        self.link_entry.set_placeholder_text(t("sys.link_ph"))
        btn_open = Gtk.Button(label=t("sys.open_game"))
        btn_open.connect("clicked", self._on_open_link)
        link_row.append(self.link_entry)
        link_row.append(btn_open)
        prof_card.append(link_row)
        outer.append(prof_card)

        # ---- diagnóstico
        lbl = Gtk.Label()
        lbl.set_markup(f"<b>{t('sys.diag')}</b>")
        lbl.set_halign(Gtk.Align.START)
        outer.append(lbl)

        self.checks_list = Gtk.ListBox()
        self.checks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.checks_list.add_css_class("boxed-list")
        outer.append(self._scrolled(self.checks_list))

        btn_refresh = Gtk.Button(label=t("sys.refresh"))
        btn_refresh.connect("clicked", lambda _b: self._refresh_checks(force=True))
        btn_refresh.set_halign(Gtk.Align.START)
        outer.append(btn_refresh)

        # ---- idioma
        lang_lbl = Gtk.Label()
        lang_lbl.set_markup(f"<b>{t('lang.label')}</b>")
        lang_lbl.set_halign(Gtk.Align.START)
        outer.append(lang_lbl)
        lang_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        _names = [t("lang.auto"), "Português (BR)", "English", "Español", "Français", "Deutsch", "Русский", "日本語"]
        self.lang_dd = Gtk.DropDown(model=Gtk.StringList.new(_names))
        saved_lang = settings.load().get("language", "auto")
        _codes = ("auto", *i18n.SUPPORTED)
        self.lang_dd.set_selected(_codes.index(saved_lang) if saved_lang in _codes else 0)
        self.lang_dd.connect("notify::selected", self._on_lang_changed)
        lang_row.append(self.lang_dd)
        lang_row.set_halign(Gtk.Align.START)
        outer.append(lang_row)
        lang_hint = Gtk.Label()
        lang_hint.set_markup(f"<small>{t('lang.restart')}</small>")
        lang_hint.set_halign(Gtk.Align.START)
        outer.append(lang_hint)

        # ---- Discord Rich Presence (recurso nativo do Sober)
        outer.append(self._build_discord_card())

        # ---- jogos (favoritos/recentes)
        outer.append(self._build_games_card())

        self._refresh_checks()
        return outer

    # ------------------------------------------------------------ card Discord (Sistema)
    def _build_discord_card(self) -> Gtk.Widget:
        """Toggle do Rich Presence nativo do Sober (mostra o jogo no Discord)."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        card.add_css_class("card")
        title = Gtk.Label()
        title.set_markup(f"<b>{t('discord.title')}</b>")
        title.set_halign(Gtk.Align.START)
        card.append(title)

        desc = Gtk.Label(label=t("discord.desc"))
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        desc.add_css_class("dim-label")
        card.append(desc)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=t("discord.show_game"))
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        self.discord_switch = Gtk.Switch()
        self.discord_switch.set_active(bool(config.read_config().get("discord_rpc_enabled", False)))
        self.discord_switch.connect("state-set", self._on_discord_toggled)
        row.append(lbl)
        row.append(self.discord_switch)
        card.append(row)
        return card

    def _on_discord_toggled(self, switch, state: bool) -> None:
        """Aplica discord_rpc_enabled na config do Sober na hora (com backup)."""
        try:
            config.write_config({"discord_rpc_enabled": bool(state)})
        except (ValueError, OSError) as exc:
            _toast(self, t("dlg.err_save"), str(exc), error=True)
            switch.set_active(not state)  # reverte em caso de erro
            return
        _toast(self, t("discord.applied"), t("sys.restart_roblox"))

    # ------------------------------------------------------------ card Jogos (Sistema)
    def _build_games_card(self) -> Gtk.Widget:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        card.add_css_class("card")
        title = Gtk.Label()
        title.set_markup(f"<b>{t('games.favorites')} / {t('games.recent')}</b>")
        title.set_halign(Gtk.Align.START)
        card.append(title)

        self.games_list = Gtk.ListBox()
        self.games_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.games_list.add_css_class("boxed-list")
        self._refresh_games_card()
        card.append(self.games_list)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_clear = Gtk.Button(label=t("games.clear"))
        btn_clear.connect("clicked", self._on_clear_history)
        row.append(btn_clear)
        row.set_halign(Gtk.Align.START)
        card.append(row)
        return card

    def _on_profile_desc(self, *args) -> None:
        key = self._selected_profile()
        self.profile_desc.set_text(t(f"desc.{key}"))

    def _on_apply_profile_now(self, _btn: Gtk.Button) -> None:
        key = self._selected_profile()
        try:
            flags = fflags.stage_preset(key)
            config.write_config({"fflags": flags})
            settings.save({"profile": key})
            _toast(self, t("sys.profile_applied", name=key), t("sys.restart_roblox"))
        except (fflags.FFFlagError, ValueError, OSError) as exc:
            _toast(self, t("dlg.err_profile"), str(exc), error=True)

    def _update_home_status(self) -> None:
        """Linha de status compacta do menu (detalhes ficam na aba Sistema)."""
        checks = getattr(self, "_last_checks", None) or environment.run_checks()
        if environment.all_ok(checks):
            self.home_status.set_text("")
            self.home_status.set_visible(False)
        else:
            fails = [c for c in checks if c.status == environment.Status.FAIL]
            names = ", ".join(c.name for c in fails)
            self.home_status.set_text(t("menu.falta", items=names))
            self.home_status.set_visible(True)

    def _selected_profile(self) -> str:
        """Id do preset (leve/medio/completo/default) — nunca a chave de tradução.

        regressão v1.4: retornava 'ff.level_medio', que o stage_preset rejeitava
        ('Preset desconhecido: ff.level_medio') ao aplicar o perfil.
        """
        idx = self.profile_dd.get_selected()
        return self.PROFILE_LABELS[min(idx, len(self.PROFILE_LABELS) - 1)][0]

    def _on_lang_changed(self, dd, _pspec) -> None:
        """Aplica o idioma na hora: salva e reconstrói menu + configuração."""
        if getattr(self, "_lang_switching", False):
            return  # sinal ecoado pela própria reconstrução
        idx = dd.get_selected()
        value = ("auto", *i18n.SUPPORTED)[min(idx, len(i18n.SUPPORTED))]
        current = settings.load().get("language", "auto")
        if value == current:
            return  # nada mudou (ex.: rebuild inicial do widget)
        settings.save({"language": value})
        i18n.set_lang(value)
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        """Reconstrói menu e janela de configuração com os textos novos."""
        self._lang_switching = True
        try:
            # janela de configuração: destrói e recria (escondida, se estava aberta)
            was_visible = bool(self.settings_win.get_visible())
            old = self.settings_win
            self.settings_win = None
            old.destroy()
            self._build_settings_window()
            if was_visible:
                self.settings_win.present()

            # menu: troca o conteúdo e o status
            self.set_child(self._build_menu_page())
        finally:
            self._lang_switching = False

    # ------------------------------------------------------------ jogos (recentes/favoritos)
    def _refresh_games_row(self) -> None:
        """Chips de jogos: favoritos primeiro, depois recentes (máx. 4)."""
        if not hasattr(self, "games_row"):
            return
        child = self.games_row.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.games_row.remove(child)
            child = nxt

        favs = history.favorites()
        entries = history.recent()
        shown: list[history.GameEntry] = []
        for pid in favs:  # favoritos primeiro
            for e in entries:
                if e.id == pid and all(s.id != pid for s in shown):
                    shown.append(e)
        for e in entries:  # depois os demais recentes
            if all(s.id != e.id for s in shown):
                shown.append(e)
        shown = shown[:4]

        if not shown:
            lbl = Gtk.Label(label=t("games.empty"))
            lbl.add_css_class("dim")
            lbl.set_halign(Gtk.Align.CENTER)
            self.games_row.append(lbl)
            return

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.CENTER)
        for e in shown:
            star = "★ " if e.id in favs else ""
            chip = Gtk.Button(label=f"{star}{e.name}")
            chip.add_css_class("game-chip")
            chip.set_tooltip_text(t("games.play_again"))
            chip.connect("clicked", self._on_chip_play, e.id)
            row.append(chip)
        self.games_row.append(row)

    def _on_chip_play(self, _btn: Gtk.Button, place_id: str) -> None:
        self._play(place_id)

    # ------------------------------------------------------------ activity tracking
    def _start_activity_watcher(self) -> None:
        """Tail dos logs do Sober em background: 'jogando agora' + histórico."""
        self._activity_watcher = activity.ActivityWatcher(
            on_change=lambda act: GLib.idle_add(self._on_activity_change, act),
            on_game_loaded=lambda act: GLib.idle_add(self._on_game_loaded, act),
        )
        self._activity_watcher.start()

    def _on_activity_change(self, act) -> bool:
        self._current_activity = act
        self._refresh_activity_row()
        return False

    def _on_game_loaded(self, act) -> bool:
        """Novo (jogo, servidor): grava no histórico de servidores + recentes."""
        try:
            if act.job_id:
                history.add_server(act.place_id, act.job_id, act.universe_id)
            history.add_recent(act.place_id, resolve=True)
        except Exception:  # noqa: BLE001 — histórico é best effort
            pass
        self._resolve_name_async(act.place_id)
        return False

    def _resolve_name_async(self, place_id: str) -> None:
        """Busca o nome real do jogo (API do Roblox) fora da main thread.

        PlaceIds já resolvidos antes são pulados (cache em memória).
        """
        cache = getattr(self, "_resolved_names", None)
        if cache is None:
            cache = self._resolved_names = set()
        if place_id in cache:
            return
        cache.add(place_id)

        def worker():
            name = history.fetch_game_name(place_id)
            if name:
                GLib.idle_add(self._on_name_resolved, place_id, name)

        threading.Thread(target=worker, daemon=True).start()

    def _on_name_resolved(self, place_id: str, name: str) -> bool:
        history.set_name(place_id, name)
        self._refresh_activity_row()
        self._refresh_servers_card()
        self._refresh_games_row()
        return False

    def _refresh_activity_row(self) -> None:
        """Card 'Jogando agora' (ou 'último servidor', com o Sober fechado)."""
        if not hasattr(self, "activity_row"):
            return
        child = self.activity_row.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.activity_row.remove(child)
            child = nxt

        act = self._current_activity
        if act is None:
            act = activity.recent_server_activity()
            self._current_activity = act

        names = {e.id: e.name for e in history.recent()}
        servers = {s["place_id"]: s.get("name") for s in history.server_history()}

        def _known(pid: str) -> str | None:
            """Nome já conhecido do jogo (recentes ou servidores); resolve na 1ª vez."""
            known = names.get(pid) or servers.get(pid)
            if known and known != pid:
                return known
            self._resolve_name_async(pid)  # best effort: vira nome real em ~1s
            return None

        if act is not None:
            name = _known(act.place_id) or t("act.unknown_game")
            lbl = Gtk.Label()
            lbl.set_markup(f"<small>🎮 {GLib.markup_escape_text(t('act.playing', name=name))}</small>")
            lbl.set_wrap(True)
            self.activity_row.append(lbl)
            if act.server_ip and not activity._is_private_ip(act.server_ip):
                loc = activity.fetch_server_location(act.server_ip)
                if loc:
                    where = ", ".join(x for x in (loc.city, loc.region, loc.country) if x)
                    if where:
                        loc_lbl = Gtk.Label()
                        loc_lbl.set_markup(f"<small>📍 {GLib.markup_escape_text(where)}</small>")
                        self.activity_row.append(loc_lbl)
            if act.job_id:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6,
                              halign=Gtk.Align.CENTER)
                btn = Gtk.Button(label=t("act.rejoin"))
                btn.add_css_class("flat")
                btn.connect("clicked", self._on_rejoin, act)
                btn_copy = Gtk.Button(label=t("act.copy"))
                btn_copy.add_css_class("flat")
                btn_copy.connect("clicked", self._on_copy_rejoin, act)
                row.append(btn)
                row.append(btn_copy)
                self.activity_row.append(row)
            return

        last = history.last_server()
        if last:
            name = _known(last["place_id"]) or last.get("name") or t("act.unknown_game")
            lbl = Gtk.Label()
            lbl.set_markup(f"<small>{GLib.markup_escape_text(t('act.last_server', name=name))}</small>")
            lbl.set_wrap(True)
            self.activity_row.append(lbl)
            btn = Gtk.Button(label=t("act.rejoin"))
            btn.add_css_class("flat")
            btn.connect("clicked", self._on_rejoin, None)
            self.activity_row.append(btn)

    def _on_rejoin(self, _btn: Gtk.Button, act) -> None:
        """Reentra no servidor atual (ou no último do histórico)."""
        url = activity.rejoin_url(act)
        if not url:
            last = history.last_server()
            if last:
                url = (f"roblox://experiences/start?placeId={last['place_id']}"
                       f"&gameInstanceId={last['job_id']}")
        if not url:
            _toast(self, t("act.rejoin"), t("act.none"), error=True)
            return
        try:
            launcher.launch_url(url)
        except launcher.LaunchError as exc:
            _toast(self, t("dlg.err_launch"), str(exc), error=True)

    def _on_copy_rejoin(self, _btn: Gtk.Button, act) -> bool:
        """Copia o link de convite do servidor atual (funciona sem Soberix)."""
        url = activity.rejoin_url(act)
        if not url:
            _toast(self, t("act.copy"), t("act.none"), error=True)
            return False
        if activity.copy_rejoin_link(act):
            _toast(self, t("act.copy"), url)
        else:
            _toast(self, t("act.copy"), t("act.copy_fail"), error=True)
        return False

    # ------------------------------------------------------------ card Servidores (Sistema)
    def _build_servers_card(self) -> Gtk.Widget:
        """Histórico de servidores visitados, com rejoin individual."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        card.add_css_class("card")
        title = Gtk.Label()
        title.set_markup(f"<b>{t('srv.title')}</b>")
        title.set_halign(Gtk.Align.START)
        card.append(title)

        self.servers_list = Gtk.ListBox()
        self.servers_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.servers_list.add_css_class("boxed-list")
        self._refresh_servers_card()
        card.append(self.servers_list)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_clear = Gtk.Button(label=t("srv.clear"))
        btn_clear.connect("clicked", self._on_clear_servers)
        row.append(btn_clear)
        row.set_halign(Gtk.Align.START)
        card.append(row)
        return card

    def _refresh_servers_card(self) -> None:
        if not hasattr(self, "servers_list"):
            return
        child = self.servers_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.servers_list.remove(child)
            child = nxt
        servers = history.server_history()
        if not servers:
            empty = Gtk.Label(label=t("srv.empty"))
            empty.set_halign(Gtk.Align.START)
            empty.set_margin_start(8)
            empty.set_margin_top(6)
            empty.set_margin_bottom(6)
            self.servers_list.append(empty)
            return
        for s in servers:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                          margin_top=4, margin_bottom=4, margin_start=8, margin_end=8)
            name = s.get("name") or s["place_id"]
            lbl = Gtk.Label()
            ts = s.get("ts") or 0
            when = time.strftime("%d/%m %H:%M", time.localtime(ts)) if ts else ""
            lbl.set_markup(f"{GLib.markup_escape_text(str(name))} <small>{when}</small>")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_max_width_chars(32)
            btn_join = Gtk.Button(label=t("srv.join"))
            btn_join.add_css_class("flat")
            btn_join.connect("clicked", self._on_join_server, s)
            btn_rm = Gtk.Button(label="✕")
            btn_rm.set_tooltip_text(t("srv.remove"))
            btn_rm.connect("clicked", self._on_remove_server, s["job_id"])
            row.append(lbl)
            row.append(btn_join)
            row.append(btn_rm)
            self.servers_list.append(row)

    def _on_join_server(self, _btn: Gtk.Button, s: dict) -> None:
        url = (f"roblox://experiences/start?placeId={s['place_id']}"
               f"&gameInstanceId={s['job_id']}")
        try:
            launcher.launch_url(url)
        except launcher.LaunchError as exc:
            _toast(self, t("dlg.err_launch"), str(exc), error=True)

    def _on_remove_server(self, _btn: Gtk.Button, job_id: str) -> bool:
        history.remove_server(job_id)
        self._refresh_servers_card()
        return False

    def _on_clear_servers(self, _btn: Gtk.Button) -> None:
        if not _confirm(self, t("srv.q_clear"), t("srv.q_clear_detail")):
            return
        history.clear_servers()
        self._refresh_servers_card()

    def _refresh_games_card(self) -> None:
        """Card de gerenciamento na aba Sistema (não bloqueia se ausente)."""
        if not hasattr(self, "games_list"):
            return
        child = self.games_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.games_list.remove(child)
            child = nxt
        favs = history.favorites()
        entries = history.recent()
        if not entries:
            empty = Gtk.Label(label=t("games.empty"))
            empty.set_halign(Gtk.Align.START)
            empty.set_margin_start(8)
            empty.set_margin_top(6)
            empty.set_margin_bottom(6)
            self.games_list.append(empty)
            return
        for e in entries:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                          margin_top=4, margin_bottom=4, margin_start=8, margin_end=8)
            star_lbl = Gtk.Label(label="★" if e.id in favs else "☆")
            name_lbl = Gtk.Label(label=e.name)
            name_lbl.set_halign(Gtk.Align.START)
            name_lbl.set_hexpand(True)
            btn_fav = Gtk.Button(label="★" if e.id not in favs else "☆")
            btn_fav.set_tooltip_text(t("games.star") if e.id not in favs else t("games.unstar"))
            btn_fav.connect("clicked", self._on_toggle_fav, e.id, e.name)
            btn_rm = Gtk.Button(label="✕")
            btn_rm.set_tooltip_text(t("games.remove"))
            btn_rm.connect("clicked", self._on_remove_game, e.id)
            row.append(star_lbl)
            row.append(name_lbl)
            row.append(btn_fav)
            row.append(btn_rm)
            self.games_list.append(row)

    def _on_toggle_fav(self, _btn: Gtk.Button, place_id: str, name: str) -> None:
        history.toggle_favorite(place_id, name)
        self._refresh_games_card()
        self._refresh_games_row()

    def _on_remove_game(self, _btn: Gtk.Button, place_id: str) -> None:
        history.remove(place_id)
        self._refresh_games_card()
        self._refresh_games_row()

    def _on_clear_history(self, _btn: Gtk.Button) -> None:
        if not _confirm(self, t("games.q_clear"), t("games.q_clear_detail")):
            return
        history.clear()
        self._refresh_games_card()
        self._refresh_games_row()

    # ------------------------------------------------------------ atualização
    def _check_updates_async(self) -> None:
        """Consulta a API do GitHub fora da main thread; bate no banner via idle_add."""
        def worker():
            info = updates.check()
            GLib.idle_add(self._show_update_banner, info)
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _show_update_banner(self, info) -> None:
        if not hasattr(self, "upd_banner"):
            return False
        if not info.found:
            self.upd_banner.set_visible(False)
            return False
        self.upd_label.set_text(t("upd.available", latest=info.latest))
        self.upd_banner.set_visible(True)
        self.upd_banner._soberix_url = info.url
        self.upd_banner._soberix_downloads = info.download_urls
        return False

    def _on_open_release(self, _btn: Gtk.Button) -> None:
        """Baixa o AppImage novo para ~/Downloads (dispara o auto-repoint do
        atalho na próxima abertura) ou, sem asset, abre a página da release."""
        urls = getattr(self.upd_banner, "_soberix_downloads", ()) or ()
        if urls:
            self._download_update_async(urls[0])
            return
        url = getattr(self.upd_banner, "_soberix_url", None) or f"https://github.com/{updates.REPO}/releases/latest"
        try:
            Gtk.show_uri(None, url, Gdk.CURRENT_TIME)
        except Exception:  # noqa: BLE001 — sem navegador: mostra o link
            _toast(self, t("upd.download"), t("upd.err_open", url=url), error=True)

    def _download_update_async(self, url: str) -> None:
        btn = self.upd_banner and next(
            (c for c in self.upd_banner if isinstance(c, Gtk.Button)), None
        )
        if btn is not None:
            btn.set_sensitive(False)

        def worker():
            ok, dest = updates.download_asset(url)
            GLib.idle_add(self._on_update_downloaded, ok, dest, btn)

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_downloaded(self, ok: bool, dest, btn) -> bool:
        if btn is not None:
            btn.set_sensitive(True)
        if ok:
            _toast(self, t("upd.done_title"), t("upd.done_detail", name=Path(dest).name))
        else:
            url = getattr(self.upd_banner, "_soberix_url", None) or f"https://github.com/{updates.REPO}/releases/latest"
            _toast(self, t("upd.download"), t("upd.err_open", url=url), error=True)
        return False

    def _play(self, place: str | None) -> None:
        checks = environment.run_checks()
        if not environment.all_ok(checks):
            fails = ", ".join(c.name for c in checks if c.status == environment.Status.FAIL)
            _toast(self, t("dlg.err_play"), t("dlg.err_play_detail", items=fails), error=True)
            return
        profile = self._selected_profile()
        try:
            flags = fflags.stage_preset(profile)
            config.write_config({"fflags": flags})
            settings.save({"profile": profile})
        except (fflags.FFFlagError, ValueError, OSError) as exc:
            _toast(self, t("dlg.err_profile"), str(exc), error=True)
            return
        try:
            place_id = launcher.extract_place_id(place) if place else None
            if place_id:
                history.add_recent(place_id, resolve=True,
                                   on_name=lambda _n: GLib.idle_add(self._refresh_games_row))
                self._refresh_games_row()
            launcher.launch(place_id)
        except launcher.LaunchError as exc:
            _toast(self, t("dlg.err_launch"), str(exc), error=True)
            return

    def _on_big_play(self, _btn: Gtk.Button) -> None:
        self._play(None)

    def _on_open_link(self, _btn: Gtk.Button) -> None:
        text = self.link_entry.get_text().strip()
        self._play(text or None)
        self.link_entry.set_text("")

    def _on_toggle_details(self, _btn: Gtk.Button) -> None:
        self.checks_revealer.set_reveal_child(not self.checks_revealer.get_reveal_child())

    def _refresh_checks(self, force: bool = False) -> None:
        """Popula a lista técnica de checagens (usa cache de 30s; force reexecuta)."""
        checks = environment.run_checks(use_cache=not force)
        self._last_checks = checks
        if not hasattr(self, "checks_list"):
            return  # aba Sistema ainda não foi construída
        child = self.checks_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.checks_list.remove(child)
            child = nxt
        icons = {environment.Status.OK: "✔", environment.Status.WARN: "⚠", environment.Status.FAIL: "✘"}
        colors = {
            environment.Status.OK: "#26a269",
            environment.Status.WARN: "#e5a50a",
            environment.Status.FAIL: "#c01c28",
        }
        for c in checks:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                          margin_top=6, margin_bottom=6, margin_start=8, margin_end=8)
            lbl = Gtk.Label()
            lbl.set_markup(
                f"<span foreground='{colors[c.status]}'>{icons[c.status]}</span>"
                f"  <b>{GLib.markup_escape_text(c.name)}</b> — "
                f"{GLib.markup_escape_text(c.detail)}"
            )
            lbl.set_halign(Gtk.Align.START)
            lbl.set_wrap(True)
            row.append(lbl)
            self.checks_list.append(row)

    def _on_launch(self, _btn: Gtk.Button) -> None:
        place = self.place_entry.get_text().strip() or None
        try:
            launcher.launch(place)
            self.place_entry.set_text("")
        except launcher.LaunchError as exc:
            _toast(self, t("dlg.err_launch"), str(exc), error=True)

    # ------------------------------------------------------------ Config
    def _build_config_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                        margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        hint = Gtk.Label()
        hint.set_markup(f"<small>{t('cfg.hint')}</small>")
        hint.set_halign(Gtk.Align.START)
        outer.append(hint)

        self.config_widgets: dict[str, Gtk.Widget] = {}
        current = config.read_config()
        rows = Gtk.ListBox()
        rows.set_selection_mode(Gtk.SelectionMode.NONE)
        rows.add_css_class("boxed-list")

        for key in sorted(config.CONFIG_SCHEMA):
            spec = config.CONFIG_SCHEMA[key]
            if key == "fflags":
                continue  # editada na aba própria
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                          margin_top=6, margin_bottom=6, margin_start=8, margin_end=8)
            label = Gtk.Label(label=key)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            row.append(label)
            if spec["type"] is bool:
                w = Gtk.Switch()
                w.set_active(bool(current.get(key, spec["default"])))
            else:
                choices = list(spec["choices"])
                w = Gtk.DropDown(model=Gtk.StringList.new(choices))
                val = current.get(key, spec["default"])
                if val in choices:
                    w.set_selected(choices.index(val))
            self.config_widgets[key] = w
            row.append(w)
            rows.append(row)

        save = Gtk.Button(label=t("cfg.save"))
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save_config)

        outer.append(self._scrolled(rows))
        outer.append(save)
        return outer

    def _on_save_config(self, _btn: Gtk.Button) -> None:
        updates: dict[str, object] = {}
        for key, widget in self.config_widgets.items():
            spec = config.CONFIG_SCHEMA[key]
            if spec["type"] is bool:
                updates[key] = widget.get_active()
            else:
                updates[key] = widget.get_model().get_string(widget.get_selected())
        try:
            config.write_config(updates)
            _toast(self, t("cfg.saved"), t("sys.restart_roblox"))
        except (ValueError, OSError) as exc:
            _toast(self, t("dlg.err_save"), str(exc), error=True)

    # ------------------------------------------------------------ FastFlags
    def _build_fflags_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                        margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        warn = Gtk.Label()
        warn.set_markup(f"<small>{t('ff.warn')}</small>")
        warn.set_halign(Gtk.Align.START)
        warn.set_wrap(True)
        outer.append(warn)

        outer.append(self._build_recommended_card())
        outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        lbl_active = Gtk.Label()
        lbl_active.set_markup(f"<b>{t('ff.active')}</b>")
        lbl_active.set_halign(Gtk.Align.START)
        outer.append(lbl_active)

        self.flags_list = Gtk.ListBox()
        self.flags_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flags_list.add_css_class("boxed-list")
        self._refresh_flags()
        outer.append(self._scrolled(self.flags_list))

        unset_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_unset = Gtk.Button(label=t("ff.remove_selected"))
        btn_unset.connect("clicked", self._on_unset_flag)
        unset_row.set_halign(Gtk.Align.START)
        unset_row.append(btn_unset)
        outer.append(unset_row)

        lbl_adv = Gtk.Label()
        lbl_adv.set_markup(f"<b>{t('ff.adv')}</b>")
        lbl_adv.set_halign(Gtk.Align.START)
        outer.append(lbl_adv)

        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        allowed_names = sorted(fflags.ALLOWED_FFLAGS)
        self.allow_dd = Gtk.DropDown(model=Gtk.StringList.new(allowed_names))
        self.allow_dd.connect("notify::selected", self._on_allow_selected)
        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text(t("ff.value_ph"))
        self.flag_hint = Gtk.Label(label="")
        self.flag_hint.set_halign(Gtk.Align.START)
        self.flag_hint.set_wrap(True)
        btn_set = Gtk.Button(label=t("ff.set"))
        btn_set.add_css_class("suggested-action")
        btn_set.connect("clicked", self._on_set_flag)
        add_box.append(self.allow_dd)
        add_box.append(self.value_entry)
        add_box.append(btn_set)
        add_box.set_hexpand(True)
        outer.append(add_box)
        outer.append(self.flag_hint)
        self._on_allow_selected()
        return outer

    # ---- card "Recomendado": níveis Leve / Médio / Completo
    def _build_recommended_card(self) -> Gtk.Widget:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        card.add_css_class("card")

        title = Gtk.Label()
        title.set_markup(f"<b>{t('ff.recommended')}</b>")
        title.set_halign(Gtk.Align.START)
        card.append(title)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, homogeneous=True)
        levels = (
            ("leve", t("ff.level_leve"), t("ff.sub_leve")),
            ("medio", t("ff.level_medio"), t("ff.sub_medio")),
            ("completo", t("ff.level_completo"), t("ff.sub_completo")),
        )
        for key, txt, sub in levels:
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            l1 = Gtk.Label()
            l1.set_markup(f"<b>{txt}</b>")
            l2 = Gtk.Label(label=sub)
            l2.add_css_class("dim-label")
            l2.set_halign(Gtk.Align.CENTER)
            inner.append(l1)
            inner.append(l2)
            btn = Gtk.Button(child=inner)
            btn.connect("clicked", self._on_level_clicked, key)
            row.append(btn)
        card.append(row)

        btn_reset = Gtk.Button(label=t("ff.reset_presets"))
        btn_reset.connect("clicked", self._on_reset_presets)
        btn_reset.set_halign(Gtk.Align.START)
        card.append(btn_reset)
        return card

    def _on_level_clicked(self, _btn: Gtk.Button, key: str) -> None:
        if not _confirm(
            self,
            t("ff.q_apply", name=key.capitalize()),
            t("ff.q_apply_detail", desc=t(f"desc.{key}")),
        ):
            return
        try:
            fflags.apply_preset(key)
            self._refresh_flags()
            _toast(self, t("ff.q_apply", name=key.capitalize()), t("sys.restart_roblox"))
        except (fflags.FFFlagError, ValueError) as exc:
            _toast(self, t("dlg.err_profile"), str(exc), error=True)

    def _on_reset_presets(self, _btn: Gtk.Button) -> None:
        if not _confirm(self, t("ff.q_reset"), t("ff.q_reset_detail")):
            return
        try:
            fflags.apply_preset("default")
            self._refresh_flags()
        except (fflags.FFFlagError, ValueError) as exc:
            _toast(self, t("dlg.err_restore"), str(exc), error=True)

    def _refresh_flags(self) -> None:
        child = self.flags_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.flags_list.remove(child)
            child = nxt
        current = fflags.current_fflags()
        if not current:
            empty = Gtk.Label(label=t("ff.empty"))
            empty.set_halign(Gtk.Align.START)
            empty.set_margin_start(8)
            empty.set_margin_top(6)
            empty.set_margin_bottom(6)
            self.flags_list.append(empty)
            return
        for name, value in sorted(current.items()):
            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1,
                              margin_top=6, margin_bottom=6, margin_start=8, margin_end=8)
            lrow = Gtk.ListBoxRow()
            lrow._soberix_flag_name = name
            lrow.set_child(row_box)
            title_lbl = Gtk.Label()
            title_lbl.set_markup(f"<b>{name}</b> = {value}")
            title_lbl.set_halign(Gtk.Align.START)
            row_box.append(title_lbl)
            entry = fflags.ALLOWED_FFLAGS.get(name)
            desc_lbl = Gtk.Label()
            desc_lbl.set_halign(Gtk.Align.START)
            if entry:
                desc_lbl.set_text(entry[1])
            else:
                desc_lbl.set_text(t("ff.not_allowed"))
            desc_lbl.add_css_class("dim-label")
            row_box.append(desc_lbl)
            self.flags_list.append(lrow)

    def _on_allow_selected(self, *args) -> None:
        name = self.allow_dd.get_model().get_string(self.allow_dd.get_selected())
        entry = fflags.ALLOWED_FFLAGS.get(name)
        if entry is None:
            self.flag_hint.set_text("")
            return
        _ftype, desc, _allowed = entry
        self.flag_hint.set_text(f"{name}: {desc} — valores: {fflags.describe_allowed(name)}")

    def _on_set_flag(self, _btn: Gtk.Button) -> None:
        name = self.allow_dd.get_model().get_string(self.allow_dd.get_selected())
        raw = self.value_entry.get_text().strip()
        try:
            fflags.set_flag(name, raw)
            self._refresh_flags()
            self.value_entry.set_text("")
        except (fflags.FFFlagError, ValueError) as exc:
            _toast(self, "Flag inválida", str(exc), error=True)

    def _on_unset_flag(self, _btn: Gtk.Button) -> None:
        row = self.flags_list.get_selected_row()
        if row is None:
            return
        name = getattr(row, "_soberix_flag_name", None)
        if not name:
            return
        fflags.remove_flag(name)
        self._refresh_flags()

    # ------------------------------------------------------------ Mods
    def _build_mods_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                        margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        hint = Gtk.Label()
        hint.set_markup(f"<small>{t('mods.hint')}</small>")
        hint.set_halign(Gtk.Align.START)
        hint.set_wrap(True)
        outer.append(hint)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_install = Gtk.Button(label=t("mods.install"))
        btn_install.add_css_class("suggested-action")
        btn_install.connect("clicked", self._on_install_mod)
        btn_remove = Gtk.Button(label=t("mods.remove"))
        btn_remove.connect("clicked", self._on_remove_mod)
        btn_clear = Gtk.Button(label=t("mods.clear"))
        btn_clear.connect("clicked", self._on_clear_mods)
        btn_row.append(btn_install)
        btn_row.append(btn_remove)
        btn_row.append(btn_clear)
        outer.append(btn_row)

        self.mods_list = Gtk.ListBox()
        self.mods_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.mods_list.add_css_class("boxed-list")
        self._refresh_mods()
        outer.append(self._scrolled(self.mods_list))
        return outer

    def _refresh_mods(self) -> None:
        child = self.mods_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.mods_list.remove(child)
            child = nxt
        installed = mods.list_mods()
        if not installed:
            empty = Gtk.Label(label=t("mods.empty"))
            empty.set_halign(Gtk.Align.START)
            empty.set_margin_start(8)
            self.mods_list.append(empty)
            return
        for m in installed:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                          margin_top=4, margin_bottom=4, margin_start=8, margin_end=8)
            lrow = Gtk.ListBoxRow()
            lrow._soberix_mod_path = m.rel_path
            lrow.set_child(row)
            lbl = Gtk.Label(label=f"{m.rel_path}  ({m.size} bytes)")
            lbl.set_halign(Gtk.Align.START)
            row.append(lbl)
            self.mods_list.append(lrow)

    def _on_install_mod(self, _btn: Gtk.Button) -> None:
        def on_open(dialog, result):
            try:
                file = dialog.open_finish(result)
            except GLib.Error:
                return
            if file is None:
                return
            try:
                installed = mods.install_zip(Path(file.get_path()))
                self._refresh_mods()
                _toast(self, t("mods.installed", n=len(installed)), t("sys.restart_roblox"))
            except mods.ModError as exc:
                _toast(self, t("mods.err_install"), str(exc), error=True)

        dialog = Gtk.FileDialog()
        filters = Gio.ListStore.new(Gtk.FileFilter)
        f = Gtk.FileFilter()
        f.set_name("Mod (.zip)")
        f.add_pattern("*.zip")
        filters.append(f)
        dialog.set_filters(filters)
        dialog.open(self, None, on_open)

    def _on_remove_mod(self, _btn: Gtk.Button) -> None:
        row = self.mods_list.get_selected_row()
        if row is None:
            return
        rel = getattr(row, "_soberix_mod_path", None)
        if not rel:
            return
        try:
            mods.remove_path(rel)
            self._refresh_mods()
        except mods.ModError as exc:
            _toast(self, t("mods.err_remove"), str(exc), error=True)

    def _on_clear_mods(self, _btn: Gtk.Button) -> None:
        if not _confirm(self, t("mods.q_clear"), t("mods.q_clear_detail")):
            return
        mods.clear_all()
        self._refresh_mods()

    # ------------------------------------------------------------ Backups
    def _build_backups_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                        margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        hint = Gtk.Label()
        hint.set_markup(f"<small>{t('bk.hint', path=constants.SOBERIX_BACKUP_DIR)}</small>")
        hint.set_halign(Gtk.Align.START)
        hint.set_wrap(True)
        outer.append(hint)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_new = Gtk.Button(label=t("bk.create"))
        btn_new.add_css_class("suggested-action")
        btn_new.connect("clicked", self._on_backup_create)
        btn_restore = Gtk.Button(label=t("bk.restore"))
        btn_restore.connect("clicked", self._on_backup_restore)
        btn_row.append(btn_new)
        btn_row.append(btn_restore)
        outer.append(btn_row)

        self.backups_list = Gtk.ListBox()
        self.backups_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.backups_list.add_css_class("boxed-list")
        self._refresh_backups()
        outer.append(self._scrolled(self.backups_list))
        return outer

    def _refresh_backups(self) -> None:
        child = self.backups_list.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.backups_list.remove(child)
            child = nxt
        infos = backups.list_backups()
        if not infos:
            empty = Gtk.Label(label=t("bk.empty"))
            empty.set_halign(Gtk.Align.START)
            empty.set_margin_start(8)
            self.backups_list.append(empty)
            return
        for info in infos:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                          margin_top=4, margin_bottom=4, margin_start=8, margin_end=8)
            lrow = Gtk.ListBoxRow()
            lrow._soberix_backup_stamp = info.stamp
            lrow.set_child(row)
            size = info.path.stat().st_size
            lbl = Gtk.Label(label=f"{info.stamp}  ({size} bytes)")
            lbl.set_halign(Gtk.Align.START)
            row.append(lbl)
            self.backups_list.append(lrow)

    def _on_backup_create(self, _btn: Gtk.Button) -> None:
        try:
            info = backups.create_backup()
            self._refresh_backups()
            _toast(self, t("bk.created"), info.path.name)
        except FileNotFoundError as exc:
            _toast(self, t("dlg.err_restore"), str(exc), error=True)

    def _on_backup_restore(self, _btn: Gtk.Button) -> None:
        row = self.backups_list.get_selected_row()
        if row is None:
            return
        stamp = getattr(row, "_soberix_backup_stamp", None)
        if not stamp:
            return
        if not _confirm(self, t("bk.q_restore"), t("bk.q_restore_detail", name=f"{stamp}.json")):
            return
        try:
            backups.restore_backup(Path(f"{stamp}.json"))
            _toast(self, t("bk.restored"), t("sys.restart_roblox"))
        except FileNotFoundError as exc:
            _toast(self, t("dlg.err_restore"), str(exc), error=True)


class SoberixApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=constants.APP_ID)

    def do_activate(self):
        # App único: clicar no ícone de novo traz a janela que já existe
        win = self.props.active_window
        if win is None:
            win = SoberixWindow(application=self)
        win.present()
        # garante ícone no tema do sistema (taskbar/dock) — idempotente
        try:
            desktop_integration.install_menu()
        except OSError:
            pass
        # Atalho desatualizado? (novo AppImage baixado, atalho apontando para o
        # binário velho) Reaponta para o mais novo encontrado nos downloads.
        try:
            upd = shortcut_refresh.refresh_shortcut()
        except Exception:  # noqa: BLE001 — conveniência, nunca deve derrubar a GUI
            upd = None
        if upd is not None:
            GLib.idle_add(
                lambda: _toast(
                    self.props.active_window,
                    t("shortcut.updated_title"),
                    t("shortcut.updated_detail", old=upd.old_exec, new=upd.new_exec),
                ) or False
            )


def run() -> int:
    # nomes de aplicativo corretos para o gerenciador de janelas (taskbar/dock)
    GLib.set_prgname("Soberix")
    GLib.set_application_name(constants.APP_NAME)
    app = SoberixApp()
    return app.run(None)
