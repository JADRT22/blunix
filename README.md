<p align="center">
  <img src="data/com.github.fernando.blunix.png" alt="Blunix logo" width="120">
</p>

<h1 align="center">Blunix</h1>

<p align="center">
  <a href="https://github.com/JADRT22/blunix/releases/latest"><img src="https://img.shields.io/github/v/release/JADRT22/blunix?style=flat-square" alt="Latest release"></a>
  <a href="https://github.com/JADRT22/blunix/stargazers"><img src="https://img.shields.io/github/stars/JADRT22/blunix?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/JADRT22/blunix/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/JADRT22/blunix/tests.yml?branch=main&style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/JADRT22/blunix/blob/main/LICENSE"><img src="https://img.shields.io/github/license/JADRT22/blunix?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/platform-Linux-fcc624?style=flat-square" alt="Platform: Linux">
</p>

<p align="center">
  An open-source Roblox launcher manager for Linux — what <a href="https://github.com/bloxstraplabs/bloxstrap">Bloxstrap</a>
  does for Windows, built on top of <a href="https://sober.vinegarhq.org/">Sober</a>.
</p>

---

**Blunix** manages [Sober](https://sober.vinegarhq.org/) — the VinegarHQ runtime that runs the
Android Roblox client natively on Linux, no Wine needed. Sober does the heavy lifting;
Blunix manages it the way Bloxstrap manages the Windows client: quality profiles, FastFlags,
mods, and backups — behind a friendly interface.

> [!WARNING]
> Since 2025-09-30, Roblox only honors FastFlags on an **allowlist** — flags outside the list
> are ignored by the client. Blunix only writes flags from the known allowlist.
> Reference: [Sober tips & tricks](https://vinegarhq.org/Sober/Configuration/TipsAndTricks.html)

## ✨ Features

- 🎮 **One-click play** — a compact menu with a big **PLAY** button; your quality profile is
  applied automatically every time you launch. No lock-in: launching Sober directly still
  works, and manually-set flags are always preserved.
- 📊 **Quality profiles** — *Light* (small change), *Medium* (balanced) and *Full* (max FPS)
  presets, each explaining exactly what it changes before applying.
- ⚡ **FastFlags editor** — allowlist-safe, with human-readable descriptions of what each
  flag does, plus manual mode for advanced users.
- 🧩 **Mod manager** — installs mod `.zip` files into Sober's `asset_overlay`
  (zip-slip protected), lists and removes them.
- 💾 **Backups** — automatic snapshots of `config.json` before every write, with restore.
- 🩺 **Doctor** — checks CPU (SSE4.1/4.2), Flatpak, Sober and Vulkan.
- 🌎 **English & Portuguese** — auto-detected from your system locale, switchable in settings.
- 🖥️ **GTK4 GUI** *and* a full **CLI** — simple for beginners, scriptable for power users.

## 📥 Install

> [!NOTE]
> **Requirement:** the [Sober](https://sober.vinegarhq.org/) Flatpak.
> ```bash
> flatpak install flathub org.vinegarhq.Sober
> ```

Grab the latest AppImage from the [**Releases**](https://github.com/JADRT22/blunix/releases/latest) page:

```bash
chmod +x Blunix-*.AppImage
./Blunix-*.AppImage
```

Double-clicking it also works (mark as executable once). New releases are built automatically
by CI — to update, download the new AppImage and replace the old one. Your settings, flags and
mods live in `~/.local/share`/`~/.local/state` and are never touched.

Optionally, register it in your applications menu (also done automatically on first launch):

```bash
./Blunix-*.AppImage install-menu
```

### Run from source

```bash
git clone https://github.com/JADRT22/blunix.git
cd blunix
python3 -m blunix            # GUI
python3 -m blunix doctor     # CLI (no GTK needed)
```

Or build your own AppImage: `./tools/build-appimage.sh`

## 🚀 Usage

The GUI opens on a small menu: **PLAY** (applies your profile and launches Roblox) and
**Settings** (quality profile, FastFlags, mods, backups, system checks, language).

For the CLI folks:

```text
blunix play                       # launch Roblox with your saved profile
blunix play 2753915549            # open a game by place ID or URL
blunix play 2753915549 --profile light | medium | full | default | off

blunix doctor                     # environment check (CPU, flatpak, Sober, Vulkan)
blunix install-menu               # create the applications-menu shortcut
blunix config show|set|reset      # official Sober config options
blunix fflags list|get|set|unset  # allowlist-safe FastFlags
blunix fflags preset light|medium|full|default
blunix mods list|install|remove|clear   # asset_overlay mods (.zip)
blunix backup create|list|restore # config.json snapshots
blunix launch [--place ID]        # plain Sober launch
```

## 🗺️ How it compares

| | Bloxstrap (Windows) | Sober (Linux) | **Blunix (Linux)** |
|---|---|---|---|
| Open source | ✅ MIT | ❌ Closed | ✅ MIT |
| Role | Manages the Windows client | Runs the Android client | Manages Sober |
| Distribution | Installer (CI-published) | Flatpak | AppImage (CI-published) |

## 🤝 Contributing

Issues and PRs are welcome! The project is pure Python (stdlib only; GTK4/PyGObject for the
GUI). Run the test suite with `python3 -m pytest`.

## 📄 License

[MIT](LICENSE) — same as Bloxstrap.

---

<p align="center">
  <sub><i>Not affiliated with Roblox Corporation or VinegarHQ.</i></sub>
</p>

<p align="center"><a href="README.pt-BR.md">🇧🇷 Leia em Português</a></p>
