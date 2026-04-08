import importlib.util
import json
from dataclasses import dataclass
from datetime import datetime

from qt_compat import PROJECT_ROOT
from tm_resources import STRINGS

CONFIG_PATH = PROJECT_ROOT / "time_master_config.py"
LEGACY_JSON_PATH = CONFIG_PATH.with_suffix(".json")


@dataclass
class AppConfig:
    target: datetime | None
    language: str
    countdown_mode: str
    countdown_start: datetime | None
    alpha: float


def clamp_alpha(value: object) -> float:
    try:
        alpha = float(value)
    except (TypeError, ValueError):
        return 0.96
    return max(0.35, min(1.0, alpha))


def parse_iso_datetime(raw: str) -> datetime | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def default_config() -> AppConfig:
    return AppConfig(None, "zh", "day", None, 0.96)


def _load_config_from_py() -> AppConfig:
    spec = importlib.util.spec_from_file_location("time_master_user_config", CONFIG_PATH)
    if spec is None or spec.loader is None:
        return default_config()

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (OSError, SyntaxError, ImportError, ValueError):
        return default_config()

    target_raw = getattr(module, "TARGET_ISO", "")
    start_raw = getattr(module, "COUNTDOWN_START_ISO", "")
    if not isinstance(target_raw, str):
        target_raw = str(target_raw) if target_raw else ""
    if not isinstance(start_raw, str):
        start_raw = str(start_raw) if start_raw else ""

    language = getattr(module, "LANGUAGE", "zh")
    if language not in STRINGS:
        language = "zh"

    return AppConfig(
        target=parse_iso_datetime(target_raw) if target_raw.strip() else None,
        language=language,
        countdown_mode="day",
        countdown_start=parse_iso_datetime(start_raw) if start_raw.strip() else None,
        alpha=clamp_alpha(getattr(module, "WIDGET_ALPHA", 0.96)),
    )


def _migrate_json_if_needed() -> None:
    if CONFIG_PATH.is_file() or not LEGACY_JSON_PATH.is_file():
        return

    try:
        data = json.loads(LEGACY_JSON_PATH.read_text(encoding="utf-8"))
        raw = data.get("target_iso")
        target = parse_iso_datetime(str(raw)) if raw else None
        if target is not None:
            save_config(AppConfig(target, "zh", "day", datetime.now(), 0.96))
        LEGACY_JSON_PATH.unlink(missing_ok=True)
    except (OSError, json.JSONDecodeError, ValueError):
        pass


def read_config() -> AppConfig:
    _migrate_json_if_needed()
    if not CONFIG_PATH.is_file():
        return default_config()

    config = _load_config_from_py()
    if config.target is not None and config.countdown_start is None:
        config.countdown_start = datetime.now()
    return config


def save_config(config: AppConfig) -> None:
    target_iso = config.target.replace(microsecond=0).isoformat(timespec="seconds") if config.target else ""
    start_iso = (
        config.countdown_start.replace(microsecond=0).isoformat(timespec="seconds")
        if config.countdown_start
        else ""
    )
    CONFIG_PATH.write_text(
        "# Time Master — editable local config\n"
        f'LANGUAGE = "{config.language}"\n'
        'COUNTDOWN_MODE = "day"  # "day" | "hour"\n'
        f"WIDGET_ALPHA = {clamp_alpha(config.alpha):.2f}\n"
        f'TARGET_ISO = "{target_iso}"\n'
        f'COUNTDOWN_START_ISO = "{start_iso}"\n',
        encoding="utf-8",
    )
