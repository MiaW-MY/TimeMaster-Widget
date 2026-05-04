# TimeMaster-Widget

A PySide6-based floating desktop countdown widget for macOS, with bilingual UI, opacity control, custom target date, optional focus sessions with fireworks on completion, per-day focus statistics, and cat-themed card styling.

**Quick links:** [Release install](#release-install-dmg-or-app) · [Run from source](#run-from-source) · [Documentation](#documentation) · [Build & publish](#build-and-publish) · [Local config](#local-config-from-source) · [Project layout](#project-layout)

## Screenshots

### Chinese

![Chinese widget screenshot](docs/images/screenshot-zh.png)

### English

![English widget screenshot](docs/images/screenshot-en.png)

## Features

- Floating always-on-top countdown card
- Chinese and English UI
- Custom target date with persistent local config
- Focus timer (minutes or hours) from settings; fireworks on successful completion
- Right-click Statistics window for the last 30 days (duration and session counts)
- Opacity adjustment
- Rounded card layout with a decorative cat asset

## Release install (DMG or app)

For **people who only downloaded a build** from GitHub Releases (not the source tree).

1. Open the **`.dmg`**, drag **Time Master** into **Applications**, eject the disk image, then launch from **Applications** or Launchpad.
2. **Settings and focus stats** live under  
   `~/Library/Application Support/TimeMaster-Widget/`  
   (`time_master_config.py` and `time_master_focus_stats.json`), not inside the app bundle.
3. **First open:** if macOS blocks an unidentified developer, use **System Settings → Privacy & Security** once, or right-click the app → **Open**.

## Run from source

For **developers** (or anyone with a `git clone`) running with a virtualenv, not the packaged `.app`.

**Requirements:** Python 3.10+, macOS.

Use Terminal **inside the project folder** (must contain `requirements.txt` and `time_master.py`). Run `pwd` and `ls requirements.txt` before creating `.venv`.

```bash
git clone <your-repo-url>
cd /path/to/TimeMaster-Widget   # e.g. cd ~/dev/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp time_master_config.example.py time_master_config.py
python3 time_master.py
```

Later: `cd` to the project, `source .venv/bin/activate`, then `python3 time_master.py`.

### Detach from Terminal (optional)

To keep the widget running **after you close Terminal**, from the project directory:

```bash
cd /path/to/TimeMaster-Widget
./start_time_master.command   # background; uses .run/
./stop_time_master.command    # stop
```

Or double-click those `.command` files in Finder.

## Documentation

| Topic | English | 中文 |
|-------|---------|------|
| Requirements | [`docs/requirements.en.md`](docs/requirements.en.md) | [`docs/requirements.zh-CN.md`](docs/requirements.zh-CN.md) |
| Architecture | [`docs/architecture.en.md`](docs/architecture.en.md) | [`docs/architecture.zh-CN.md`](docs/architecture.zh-CN.md) |

Personal or local-only notes (`docs/usage.*`, `docs/release.*`, `docs/known-issues.md`, `docs/private/`, etc.) are listed in [`.gitignore`](.gitignore) and are not pushed to GitHub.

## Build and publish

For **maintainers** who produce the **`.app` / DMG** and attach them to **GitHub Releases**. Download-only users can skip this.

Use the **same venv** as in [Run from source](#run-from-source) (`source .venv/bin/activate`, dependencies installed). From the project root:

```bash
./scripts/build_mac_app.sh
```

Writes `dist/Time Master.app` via PyInstaller (see `requirements-dev.txt`).

**Common mistake:** creating `.venv` in `$HOME` instead of the repo — remove `~/.venv` if needed, then `cd` into the project and create `.venv` again.

**App icon:** `assets/AppIcon.icns` from `assets/app_icon_1024.png`. Prefer a **square** 1024×1024 with no thick empty margin; run `python3 scripts/make_app_icon.py` after `pip install -r requirements-dev.txt`, then rebuild the app.

**Gatekeeper:** unsigned builds may need **Privacy & Security** (or right-click → **Open**) until you code-sign for distribution.

### DMG

```bash
./scripts/build_dmg.sh
```

Uncompressed read-only DMG (`UDRO`) with the **`.app`** and an **Applications** alias → `dist/Time-Master-<version>.dmg` (`git describe` or `VERSION=1.0.0 ./scripts/build_dmg.sh`). Builds the `.app` first if missing.

### Ship on GitHub

1. Commit and push.
2. `git tag v1.0.0 && git push origin v1.0.0` (your version).
3. **Releases → Draft a new release** → choose tag → attach `dist/Time-Master-*.dmg`.
4. In the description: **macOS version tested**, **Apple Silicon vs Intel** for the build host, and short steps for downloaders (same ideas as [Release install](#release-install-dmg-or-app)).

**Day-to-day:** branch on `main`, iterate with `python3 time_master.py`, then rebuild and attach DMG when you cut a release. Config while developing lives next to the repo; the packaged app uses Application Support — copy files manually if you migrate between the two.

## Local config (from source)

From a **clone**, settings are in `time_master_config.py` (ignored by Git):

```bash
cp time_master_config.example.py time_master_config.py
```

Fields: `LANGUAGE`, `WIDGET_ALPHA`, `TARGET_ISO`, `COUNTDOWN_START_ISO`, `FOCUS_DURATION_SECONDS`, `FOCUS_STARTED_ISO` (see `time_master_config.example.py` for shapes).

Focus stats: `time_master_focus_stats.json` in the project directory (ignored). **Packaged app:** both paths are under `~/Library/Application Support/TimeMaster-Widget/` — see [Release install](#release-install-dmg-or-app).

## Project layout

- **`assets/`** — committed images and `AppIcon.icns` loaded at runtime.
- **`time_master.py`** — entry; **`tm_app.py`** / **`tm_ui.py`** / **`tm_config.py`** / **`tm_resources.py`** / **`qt_compat.py`** — app, UI, config, constants, Qt paths.
- **`scripts/build_mac_app.sh`** — `dist/Time Master.app`; **`scripts/build_dmg.sh`** — DMG; **`scripts/make_app_icon.py`** — refresh `AppIcon.icns`.
- **`docs/`** — in-repo **requirements** + **architecture**; other doc filenames are gitignored for local use (see [Documentation](#documentation)).

macOS-only; standard `pip` workflow (no committed `.pyside6_vendor/`). Do not commit `time_master_config.py` or personal stats files.
