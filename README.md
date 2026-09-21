<p align="center">
  <img src="data/com.github.fernando.soberix.png" alt="Soberix logo" width="120">
</p>

<h1 align="center">Soberix</h1>

<p align="center">
  <a href="https://github.com/JADRT22/soberix/releases/latest"><img src="https://img.shields.io/github/v/release/JADRT22/soberix?style=flat-square" alt="Latest release"></a>
  <a href="https://github.com/JADRT22/soberix/stargazers"><img src="https://img.shields.io/github/stars/JADRT22/soberix?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/JADRT22/soberix/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/JADRT22/soberix/tests.yml?branch=main&style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/JADRT22/soberix/blob/main/LICENSE"><img src="https://img.shields.io/github/license/JADRT22/soberix?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/platform-Linux-fcc624?style=flat-square" alt="Platform: Linux">
</p>

<p align="center">
  An open-source Roblox launcher manager for Linux — what <a href="https://github.com/bloxstraplabs/bloxstrap">Bloxstrap</a>
  does for Windows, built on top of <a href="https://sober.vinegarhq.org/">Sober</a>.
</p>

<p align="center">
  <a href="https://jadrt22.github.io/soberix/"><b>🌐 Website</b></a> ·
  <a href="https://github.com/JADRT22/soberix/releases/latest"><b>⬇ Download</b></a>
</p>

---

**Soberix** manages [Sober](https://sober.vinegarhq.org/) — the VinegarHQ runtime that runs the
Android Roblox client natively on Linux, no Wine needed. Sober does the heavy lifting;
Soberix manages it the way Bloxstrap manages the Windows client: quality profiles, FastFlags,
mods, activity tracking and backups — behind a friendly interface.

> [!WARNING]
> Since 2025-09-30, Roblox only honors FastFlags on an **allowlist** — flags outside the list
> are ignored by the client. Soberix only writes flags from the known allowlist.
> Reference: [Sober tips & tricks](https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html)

## ✨ Features

- 🎮 **One-click play** — a compact menu with a big **PLAY** button; your quality profile is
  applied automatically every time you launch. No lock-in: launching Sober directly still
  works, and manually-set flags are always preserved.
- 🕹️ **Activity tracking** — shows what you're playing (real game name, resolved via
  Roblox's public API) and lets you **rejoin the exact server** you were on, even after
  closing Sober — plus a visited-servers history and taskbar quick actions (Play / Rejoin).
- ⭐ **Recent & favorite games** — chips on the home screen to replay a game with one click.
- 🔄 **Update checker** — pings GitHub Releases and **downloads the new AppImage** into
  `~/Downloads`; the menu shortcut repoints itself when you open the new version.
- 📊 **Quality profiles** — *Light* (small change), *Medium* (balanced) and *Full* (max FPS)
  presets, each explaining exactly what it changes before applying.
- ⚡ **FastFlags editor** — allowlist-safe, with human-readable descriptions of what each
  flag does, plus manual mode for advanced users.
- 🧩 **Mod manager** — installs mod `.zip` files into Sober's `asset_overlay`
  (zip-slip protected), lists and removes them — plus **1-click popular mods**
  (embedded mute death sound; classic sounds/cursors as soon as a community mirror exists).
- 💾 **Backups** — automatic snapshots of `config.json` before every write, with restore.
- 🩺 **Doctor** — checks CPU (SSE4.1/4.2), Flatpak, Sober and Vulkan.
- 🌎 **7 languages** — English, Português, Español, Français, Deutsch, Русский, 日本語:
  auto-detected from your system locale, switchable instantly in settings.
- 💬 **Discord Rich Presence** — one switch to show what you're playing on Discord
  (native Sober feature, managed with a backup-safe toggle).
- 🖥️ **GTK4 GUI** *and* a full **CLI** — simple for beginners, scriptable for power users.

## 🤔 Why not "just use Bloxstrap"?

- **Bloxstrap is Windows-only** (WPF/.NET) and relies on Windows mechanisms (registry,
  `ClientSettings/ClientAppSettings.json`, the `Modifications/` folder) — and it is no
  longer under active development.
- On Linux the right foundation is **Sober** (Flatpak `org.vinegarhq.Sober`), which runs
  the **Android** Roblox client natively — no Wine, no translation layer.
- Sober is closed-source and Flatpak-only; the correct integration points are its
  documented `config.json` and `asset_overlay` — exactly what Soberix manages.

## 📥 Install

> Full overview, screenshots and FAQ on the **[website](https://jadrt22.github.io/soberix/)**.

> [!NOTE]
> **Requirement:** the [Sober](https://sober.vinegarhq.org/) Flatpak.
> ```bash
> flatpak install flathub org.vinegarhq.Sober
> ```

Grab the latest AppImage from the [**Releases**](https://github.com/JADRT22/soberix/releases/latest) page:

```bash
chmod +x Soberix-*.AppImage
./Soberix-*.AppImage
```

Double-clicking it also works (mark as executable once). New releases are built automatically
by CI — to update, download the new AppImage and replace the old one (the update banner can
download it for you). Your settings, flags and mods live in `~/.local/share`/`~/.local/state`
and are never touched.

Optionally, register it in your applications menu (also done automatically on first launch):

```bash
./Soberix-*.AppImage install-menu
```

### Requirements

- Linux x86_64 with SSE4.1 and SSE4.2 (`grep -o sse4_1 /proc/cpuinfo`)
- [Flatpak](https://flatpak.org/) with Flathub configured, plus the Sober Flatpak
- Python 3.11+ with PyGObject/GTK 4 when running from source:
  - Arch/CachyOS: `sudo pacman -S python-gobject gtk4`
  - Debian/Ubuntu: `sudo apt install python3-gi gir1.2-gtk-4.0`

### Run from source

```bash
git clone https://github.com/JADRT22/soberix.git
cd soberix
python3 -m soberix            # GUI
python3 -m soberix doctor     # CLI (no GTK needed)
```

Or build your own AppImage: `./tools/build-appimage.sh`

## 🚀 Usage

The GUI opens on a small menu: **PLAY** (applies your profile and launches Roblox) and
**Settings** (quality profile, FastFlags, mods, servers, backups, system checks, language).

For the CLI folks:

```text
soberix play                       # launch Roblox with your saved profile
soberix play 2753915549            # open a game by place ID or URL
soberix play 2753915549 --profile light|medium|full|default|off

soberix doctor                     # environment check (CPU, flatpak, Sober, Vulkan)
soberix install-menu               # create the applications-menu shortcut
soberix config show|set|reset      # official Sober config options
soberix fflags list|get|set|unset  # allowlist-safe FastFlags
soberix fflags preset leve|medio|completo|default  # quality presets (pt names)
soberix mods list|install|remove|clear   # asset_overlay mods (.zip)
soberix mod-presets [id]           # popular mods (mute death sound works offline)
soberix games                      # recent games (* = favorite)
soberix status                     # game/server currently detected in Sober's logs
soberix rejoin                     # reopen the last server you were on
soberix servers                    # visited servers (with rejoin links)
soberix backup create|list|restore # config.json snapshots
soberix launch [--place ID]        # plain Sober launch
```

## 🔧 How Soberix modifies Sober

| What           | Mechanism                                                       |
|----------------|-----------------------------------------------------------------|
| Config/fflags  | `~/.var/app/org.vinegarhq.Sober/config/sober/config.json`       |
| Mods           | `~/.var/app/org.vinegarhq.Sober/data/sober/asset_overlay/`      |
| Backups        | `~/.local/share/soberix/backups/`                               |
| Soberix state  | `~/.local/state/soberix/` (settings, history, log)              |

Sober only reads its config at boot: after changing anything, close and reopen Roblox
(applies to FastFlags and mods).

## 🗺️ How it compares

| | Bloxstrap (Windows) | Sober (Linux) | **Soberix (Linux)** |
|---|---|---|---|
| Open source | ✅ MIT | ❌ Closed | ✅ MIT |
| Role | Manages the Windows client | Runs the Android client | Manages Sober |
| Distribution | Installer (CI-published) | Flatpak | AppImage (CI-published) |

## 🔒 Security & privacy

- The app never reads or transmits your Roblox session cookie (`cookies`, `state`).
- Backups contain only `config.json`.
- No telemetry. 100% open source. Activity tracking reads Sober's local log files only.
- Mods are `.zip` files you provide (or the embedded offline preset), zip-slip protected.

## ⚠️ Legal & limitations

- Soberix is **not affiliated** with Roblox Corporation or VinegarHQ.
- Unofficial clients can in theory violate Roblox's ToS; VinegarHQ states normal Sober use
  "very rarely" triggers moderation. Use at your own risk. No multi-instance, bots or exploits —
  Sober blocks multi-instance by design.
- **FastFlags**: only the post-2025-09-30 allowlist works; Roblox can change it at any time.
- **Studio**: Sober doesn't run Roblox Studio (use Vinegar via Wine for that).

## 🤝 Contributing

Issues and PRs are welcome! The project is pure Python (stdlib only; GTK4/PyGObject for the
GUI). Run the test suite with `python3 -m pytest` (the GUI smoke tests need GTK4/Xvfb).

## 📄 License

[MIT](LICENSE) — same as Bloxstrap.

---

<p align="center">
  <sub><i>Not affiliated with Roblox Corporation or VinegarHQ.</i></sub>
</p>

<p align="center"><a href="README.pt-BR.md">🇧🇷 Leia em Português</a></p>
