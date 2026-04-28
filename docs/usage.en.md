# Time Master Usage Guide

## 1. First-Time Setup

Run the following inside the project directory:

```bash
cd TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp time_master_config.example.py time_master_config.py
python3 time_master.py
```

## 2. Daily Launch

For normal daily use:

```bash
cd TimeMaster-Widget
source .venv/bin/activate
python3 time_master.py
```

If you do not want the widget tied to the current Terminal session, use the bundled launcher instead:

```bash
cd TimeMaster-Widget
./start_time_master.command
```

This runs the widget in the background, so closing Terminal will not close the widget.

To stop it:

```bash
cd TimeMaster-Widget
./stop_time_master.command
```

You can also double-click these `.command` files in Finder on macOS.

## 3. UI Interactions

- Drag the widget with left click
- Double-click to open settings
- Right-click to open the menu
- Open Statistics from the menu to review the last 30 days of focus data
- Switch between Chinese and English from the menu
- Quit from the menu

## 4. Supported Settings

The current widget supports:

- Target date
- Focus duration in minutes or hours (leave empty to skip starting a new session; saving starts immediately; minimum 1 minute)
- Opacity
- Interface language

Settings are stored in the local `time_master_config.py`.

Focus statistics are stored in `time_master_focus_stats.json` (per-day seconds and session counts). This file is ignored by Git by default.

## 5. Local Config Files

Config example:

- `time_master_config.example.py`

Real local runtime config:

- `time_master_config.py`

Common fields:

- `LANGUAGE`
- `WIDGET_ALPHA`
- `TARGET_ISO`
- `COUNTDOWN_START_ISO`
- `FOCUS_DURATION_SECONDS`
- `FOCUS_STARTED_ISO`

## 6. Common Issues

### Python says the file does not exist

This usually means you ran the command outside the project directory.

Correct usage:

```bash
cd TimeMaster-Widget
python3 time_master.py
```

### Closing Terminal also closes the widget

Use:

```bash
cd TimeMaster-Widget
./start_time_master.command
```

This launcher detaches the widget from the current Terminal session and keeps it running in the background.

### English layout does not match Chinese exactly

This is intentional. English uses its own layout offsets because the strings are longer and need separate tuning.

### Config changes do not apply

Make sure:

- You edited `time_master_config.py`
- The file is valid Python assignment syntax
- Datetime values use ISO format

## 7. If You Want to Modify the Project Later

Most common edit locations:

- Size / colors / strings: `tm_resources.py`
- Main app behavior: `tm_app.py`
- Bars / dialog / card painting: `tm_ui.py`
- Config behavior: `tm_config.py`
