# TimeMaster-Widget

A PySide6-based floating desktop countdown widget for macOS, with bilingual UI, opacity control, custom target date, optional focus sessions with fireworks on completion, per-day focus statistics, and cat-themed card styling.

## Screenshots

### Chinese

![Chinese widget screenshot](docs/images/screenshot-zh.png)

### English

![English widget screenshot](docs/images/screenshot-en.png)

## Quick Start

**Use Terminal inside the project folder** — the one that contains `requirements.txt` and `time_master.py`. If `cd TimeMaster-Widget` fails, you are not in the parent of that folder (for example the repo may live at `~/dev/TimeMaster-Widget`). Run `pwd` and `ls requirements.txt` to confirm before creating `.venv`.

```bash
git clone <your-repo-url>
cd /path/to/TimeMaster-Widget   # e.g. cd ~/dev/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp time_master_config.example.py time_master_config.py
python3 time_master.py
```

## Features

- Floating always-on-top countdown card
- Chinese and English UI
- Custom target date with persistent local config
- Focus timer (minutes or hours) from settings; fireworks on successful completion
- Right-click Statistics window for the last 30 days (duration and session counts)
- Opacity adjustment
- Rounded card layout with a decorative cat asset

## Documentation

- Chinese requirements: `docs/requirements.zh-CN.md`
- Chinese architecture: `docs/architecture.zh-CN.md`
- Chinese usage: `docs/usage.zh-CN.md`
- English requirements: `docs/requirements.en.md`
- English architecture: `docs/architecture.en.md`
- English usage: `docs/usage.en.md`

## Requirements

- Python 3.10+
- macOS

## Install

```bash
cd /path/to/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Run

```bash
cd /path/to/TimeMaster-Widget
python3 time_master.py
```

## Easier Launch On macOS

If you do not want to keep the widget attached to a Terminal session, you can use the bundled launcher files (from the project directory):

```bash
cd /path/to/TimeMaster-Widget
./start_time_master.command
```

This starts the widget in the background, writes runtime data into `.run/`, and lets you close Terminal afterward without closing the widget.

To stop it:

```bash
cd /path/to/TimeMaster-Widget
./stop_time_master.command
```

You can also double-click `start_time_master.command` and `stop_time_master.command` in Finder.

## Standalone app (no Python on your Mac)

To ship or use a normal macOS app that does **not** rely on Terminal or a system Python install, build a `.app` bundle once on your machine:

```bash
cd /path/to/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
./scripts/build_mac_app.sh
```

If you already ran `python3 -m venv .venv` from your home directory by mistake, remove that stray `~/.venv` (or `rm -rf ~/.venv`) so it does not confuse you; then create `.venv` again **after** `cd` into the real project folder.

This installs PyInstaller (see `requirements-dev.txt`) and writes `dist/Time Master.app`. You can open that app from Finder or drag it to **Applications**. Double-clicking starts the widget like any other app.

**App icon:** the build uses `assets/AppIcon.icns`. macOS draws the same rounded “squircle” shape as other apps; your PNG should be a **full square** (1024×1024 or close) with **no wide dark margin** around a small panel—use a full-bleed export, or let `scripts/make_app_icon.py` trim dark frames and flatten transparency onto the card color. To refresh: replace `assets/app_icon_1024.png`, run `python3 scripts/make_app_icon.py` (after `pip install -r requirements-dev.txt`), then `./scripts/build_mac_app.sh`.

**Config and data when using the .app:** settings and focus statistics are stored under  
`~/Library/Application Support/TimeMaster-Widget/`  
(`time_master_config.py` and `time_master_focus_stats.json`), not inside the app bundle.

**Code signing / Gatekeeper:** unsigned local builds may trigger “cannot be opened” until you allow them in **System Settings → Privacy & Security**, or you sign the app with your Apple Developer ID when you are ready to distribute.

## Continuing product development

Typical iteration loop:

1. **Clone / branch** — work on `main` or a feature branch; commit small, reviewable changes.
2. **Dev environment** — keep a project virtualenv (`.venv`), `pip install -r requirements.txt`, run `python3 time_master.py` for fast reload during UI work.
3. **Rebuild the .app** — after meaningful releases, run `./scripts/build_mac_app.sh` again and replace the copy in Applications (or bump a version label in your own release notes).
4. **User data** — while developing from source, config still lives next to the repo (see below). The standalone app uses Application Support; copy files between those locations if you need to migrate manually.

## Local Config

The app stores runtime settings in a local `time_master_config.py` file, which is intentionally ignored by Git.

You can create it from the example:

```bash
cp time_master_config.example.py time_master_config.py
```

Supported fields:

- `LANGUAGE`: `"zh"` or `"en"`
- `WIDGET_ALPHA`: `0.35` to `1.00`
- `TARGET_ISO`: target datetime in ISO format
- `COUNTDOWN_START_ISO`: countdown start datetime in ISO format
- `FOCUS_DURATION_SECONDS`: active focus session length in seconds (`0` when idle)
- `FOCUS_STARTED_ISO`: focus session start time in ISO format

Focus statistics are stored in `time_master_focus_stats.json` in the project directory (ignored by Git).

## Assets

Required image assets live in `assets/` and are committed to the repository because the widget depends on them at runtime.

## Project Structure

- `time_master.py`: entry point
- `tm_app.py`: main window and app behavior
- `tm_ui.py`: UI widgets and custom drawing
- `tm_config.py`: local config loading and saving
- `tm_resources.py`: strings, colors, size constants, layout parameters
- `qt_compat.py`: Qt import compatibility, resource vs data paths (dev vs bundled app)
- `assets/`: runtime images and `AppIcon.icns` (standalone app icon)
- `scripts/build_mac_app.sh`: builds `dist/Time Master.app` with PyInstaller
- `scripts/make_app_icon.py`: regenerates `AppIcon.icns` from `assets/app_icon_1024.png`
- `docs/`: bilingual project documentation

## Notes

- The current UI is tuned for macOS desktop usage.
- The repository uses standard Python dependency management for publishing and does not require committing `.pyside6_vendor/`.
- The real local runtime config file `time_master_config.py` should not be committed.
