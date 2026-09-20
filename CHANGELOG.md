# Changelog

All notable changes to Soberix are documented here, newest first.
Format inspired by [Bloxstrap's release notes](https://github.com/bloxstraplabs/bloxstrap/releases).

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
