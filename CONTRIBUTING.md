# Contributing to Blunix

Thanks for your interest in improving Blunix! Issues and pull requests are welcome.

## Ways to help

- 🐞 [Report a bug](../../issues/new?template=bug_report.md)
- 💡 [Suggest a feature](../../issues/new?template=feature_request.md)
- 🌎 Improve translations (PT/EN strings live in `blunix/i18n.py`)
- 💻 Code — bug fixes, new features, distro compatibility

## Development setup

```bash
git clone https://github.com/JADRT22/blunix.git
cd blunix

# GUI needs GTK4 + PyGObject (on Debian/Ubuntu):
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Run the test suite (no GUI needed):
python3 -m pytest

# Run the app from source:
python3 -m blunix            # GUI
python3 -m blunix doctor     # CLI
```

## Ground rules

- **Python stdlib only** for core modules — GTK4/PyGObject is imported only by the GUI.
  Don't add third-party runtime dependencies.
- **FastFlags**: only write flags inside the allowlist (`blunix/fflags.py`). Roblox ignores
  everything else since 2025-09-30.
- **Never touch user data destructively**: writes to the Sober `config.json` must go through
  `config.write_config` (it snapshots a backup first).
- **GUI strings** must go through `i18n.t()` — every key needs both PT and EN entries
  (a test enforces this).
- Match the existing code style; keep changes focused — one PR per feature/fix.

## Pull request checklist

- [ ] `python3 -m pytest` passes locally
- [ ] Tests included for new behavior
- [ ] User-facing strings are translated (PT + EN)
- [ ] Works when running from source **and** inside the AppImage

The maintainers merge to `main`; releases are tag-driven (`v*`) and built by CI.
