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

## 3. UI Interactions

- Drag the widget with left click
- Double-click to open settings
- Right-click to open the menu
- Switch between Chinese and English from the menu
- Quit from the menu

## 4. Supported Settings

The current widget supports:

- Target date
- Opacity
- Interface language

Settings are stored in the local `time_master_config.py`.

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

## 6. Common Issues

### Python says the file does not exist

This usually means you ran the command outside the project directory.

Correct usage:

```bash
cd TimeMaster-Widget
python3 time_master.py
```

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
