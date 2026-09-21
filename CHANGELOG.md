# Changelog

All notable changes to Soberix are documented here, newest first.
Format inspired by [Bloxstrap's release notes](https://github.com/bloxstraplabs/bloxstrap/releases).

## v1.6.2

Bug fixes

- Fixed the release CI (for real this time): each smoke test now creates a
  Gtk.Application with a unique id and no D-Bus registration — two apps
  with the same id collided on the session bus ("object already exported").
  Verified locally with pytest on the system Python: 3/3 pass

## v1.6.1

Bug fixes

- Fixed the release CI: the new GUI smoke tests called `Gtk.init()` and
  checked its return, but PyGObject returns `None` — the check now uses
  `Gtk.is_initialized()` (validated locally against the system Python)

## v1.6

The mods & quick actions release.

Additions

- **Popular mods, 1 click**: the Mods tab now offers classic community
  mods — old death sounds (2006/2013) and the 2006 cursor set — installed
  with one button (CLI: `soberix mod-presets [id]`), with per-file
  fallback when the network fails
- **Taskbar quick actions**: the app icon's right-click menu gains
  Play / Rejoin last server / Servers & history (desktop actions)
- **GUI smoke tests** on CI (Xvfb): the real GTK window is built on every
  push — would have caught the v1.5.1 "app not opening" regression

## v1.5.2

Bug fixes

- Fixed the app not opening at all (v1.5.1 regression): a lost assignment in
  the game-name resolver crashed the menu build with `UnboundLocalError` —
  the window never appeared and no shortcut worked

## v1.5.1

Polish for the activity tracking release.

Additions

- **Real game names everywhere**: the "Playing now" card, the new Servers
  tab and the home chips show the game's official name (resolved in the
  background via Roblox's public API) instead of a raw place ID —
  "Brookhaven RP", not "136406881576517"
- **Servers tab**: the last 30 visited servers with per-server Join,
  remove and clear — the Bloxstrap-style server history
- **Copy invite link** button next to Rejoin (wl-copy/xclip/xsel)
- **Server location on the card** when the log exposes a public IP
- New CLI command: `soberix servers`

## v1.5

The activity tracking release.

Additions

- **Real game names everywhere**: the "Playing now" card, the servers tab and
  the home chips show the game's official name (resolved via Roblox's public
  API in the background) instead of a raw place ID — "Brookhaven RP", not
  "136406881576517"
- **Servers tab**: the last 30 visited servers with per-server Join, remove
  and clear — the Bloxstrap-style server history
- **Copy invite link** button next to Rejoin (uses wl-copy/xclip/xsel)
- **Server location on the card**: shows city/region/country when the log
  exposes a public server IP (ipinfo.io)
- New CLI command: `soberix servers` (visited servers with timestamps)

- **Activity tracking** (the Bloxstrap-style feature Soberix was missing):
  Soberix now reads the Sober's own logs (`sober_logs/latest.log`) to detect
  which game and server you are on — no background spy process, just log
  parsing. The home menu shows a **"Playing now"** card with a
  **↻ Rejoin server** button that reopens the exact server you were on
  (`roblox://…&gameInstanceId=…`)
- **Server history** (`game_servers.json`): the last 30 visited servers are
  recorded while you play, so **rejoin works even after closing Sober**
- New CLI commands: `soberix status` (detected game/server, uptime),
  `soberix rejoin` (`--now` for the live session) and `soberix where`
  (server location when the log exposes a public IP)
- The update banner's **Download button now downloads the new AppImage**
  straight into `~/Downloads` (atomic write, executable bit set) — opening
  it then triggers the automatic shortcut repoint. Falls back to opening
  the release page when there is no asset

Bug fixes

- Fixed "Erro ao aplicar o perfil: Preset desconhecido: 'ff.level_medio'"
  (v1.4 regression): the translated quality-profile dropdown passed its
  translation key instead of the preset id, so applying a profile from the
  System tab always failed

## v1.4.2

Additions

- **Self-updating menu shortcut**: on startup (when running from an AppImage),
  Soberix looks for a newer `Soberix-*.AppImage` in the standard download
  folders and repoints the applications-menu shortcut to it — no more stale
  shortcuts launching the old binary after you download an update. A toast
  confirms the change (translated in all 7 languages)

## v1.4.1

Bug fixes

- Fixed the internal version stuck at 1.3: the v1.4 AppImage shipped with
  `VERSION=1.3`, so the update checker offered the same release to users who
  already had it. Now correctly reports 1.4.1 and offers the update to
  everyone on v1.4 or older
- The version now lives in a single place (`soberix/constants.py`) —
  `pyproject.toml` reads it via a setuptools dynamic attr and the AppImage
  build extracts it, so the package, the AppImage and the update checker
  can no longer diverge

## v1.4

The website & polish release.

Additions

- **Official website**: <https://jadrt22.github.io/soberix/> — overview with animated
  background, feature showcase, screenshots, install steps and FAQ (GitHub Pages,
  linked from the README and the repo homepage)

Changes

- Quality profile names (Light / Medium / Full / Default) are now translated in all
  seven languages — the dropdown no longer shows hardcoded Portuguese words
- Launcher shortcut no longer silently fails when opened from the app menu: the
  chosen Python is verified to have PyGObject and the Exec line embeds PYTHONPATH

Bug fixes

- Fixed the app not opening from the desktop menu (two silent failure modes:
  venv without `gi`, and `python -m soberix` failing outside the project folder)

## v1.3

The languages release.

Additions

- **Five new languages**: Español, Français, Deutsch, Русский and 日本語 —
  every string of the app translated (a test enforces full parity),
  auto-detected from the system locale and switchable instantly in settings
- **Discord Rich Presence card** in System settings: one switch to show that
  you're playing Roblox (with the current game's name) on Discord — a native
  Sober feature (`discord_rpc_enabled`), applied immediately with backup

## v1.2

The rename release. Formerly known as **Blunix** — the name changed to **Soberix**
to avoid conflicting with an existing Linux consulting company (Blunix GmbH, Berlin)
and to make the Sober connection explicit.

Changes

- Project renamed to **Soberix** (package, app-id, icon, AppImage, repo)
- The menu window now scales with the monitor resolution and desktop zoom
  (no longer tiny on 1440p/4K or HiDPI)
- GitHub repo moved to `JADRT22/soberix` (old links redirect)

Note: users of Blunix ≤ 1.1 will see the built-in update checker offer v1.2 —
the AppImage binary name changes from `Blunix-*.AppImage` to `Soberix-*.AppImage`.

## v1.1

The bugfix release — everything found in a full manual review of the codebase.

Bug fixes

- Fixed a crash when pasting an invalid link in the "open game" field (the error escaped the error-handling block)
- Fixed a game being added to Recents even when it failed to launch
- Fixed removing the wrong flag/mod/backup in some cases (lists now carry real identifiers instead of re-parsing label text)
- Fixed path check in `mods remove` that could false-positive on sibling directories (now `Path.is_relative_to`)
- Fixed the GUI freezing on cold start (system checks ran up to 3× per launch; now cached for 30s)
- Fixed the taskbar icon cache being force-rebuilt on every window activation (now only when the shortcut content changes)
- Language switch now applies instantly — no restart needed

Changes

- The `.desktop` entry is now fully in English (GenericName/Comment/Keywords)
- Recent games now resolve the real game name via Roblox's public API, so chips show "Brookhaven RP" instead of "2753915549"

## v1.0

The first stable release.

Additions

- **Recent & favorite games**: one-click replay chips on the home menu (favorites first, starred), manager card in System, `soberix games` CLI listing
- **Update checker**: background check against GitHub Releases with a download banner — never blocks or crashes offline
- **Quality profiles**: Light / Medium / Full presets applied automatically when pressing PLAY (no lock-in; Sober keeps working standalone and manual flags are preserved)
- **FastFlags editor**: allowlist-safe (post-2025-09-30) with human-readable descriptions, plus the "Recommended" card with three impact levels
- **Mod manager**: `.zip` mods into Sober's `asset_overlay`, zip-slip protected
- **Backups**: automatic `config.json` snapshots before every write, with restore
- **Doctor**: checks CPU (SSE4.1/4.2), Flatpak, Sober and Vulkan
- **English & Portuguese**: auto-detected from the system locale, switchable instantly in settings
- **AppImage distribution**: single-file executor built and published by CI on every tag
