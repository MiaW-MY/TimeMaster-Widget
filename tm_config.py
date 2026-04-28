import importlib.util
import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any

from qt_compat import PROJECT_ROOT
from tm_resources import STRINGS

CONFIG_PATH = PROJECT_ROOT / "time_master_config.py"
LEGACY_JSON_PATH = CONFIG_PATH.with_suffix(".json")
FOCUS_STATS_PATH = PROJECT_ROOT / "time_master_focus_stats.json"


@dataclass
class AppConfig:
    target: datetime | None
    language: str
    countdown_mode: str
    countdown_start: datetime | None
    alpha: float
    focus_duration_seconds: int = 0
    focus_started_at: datetime | None = None


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
    return AppConfig(None, "zh", "day", None, 0.96, 0, None)


def _focus_end_at(config: AppConfig) -> datetime | None:
    if config.focus_duration_seconds <= 0 or config.focus_started_at is None:
        return None
    return config.focus_started_at + timedelta(seconds=config.focus_duration_seconds)


def _normalize_focus_if_expired(config: AppConfig) -> AppConfig:
    end = _focus_end_at(config)
    if end is None:
        return config
    if datetime.now() < end:
        return config
    record_focus_completion(config.focus_duration_seconds)
    cleared = replace(config, focus_duration_seconds=0, focus_started_at=None)
    save_config(cleared)
    return cleared


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
    target_start_date_raw = getattr(module, "TARGET_START_ISO", "")
    if not isinstance(target_raw, str):
        target_raw = str(target_raw) if target_raw else ""
    if not isinstance(start_raw, str):
        start_raw = str(start_raw) if start_raw else ""
    if not isinstance(target_start_date_raw, str):
        target_start_date_raw = str(target_start_date_raw) if target_start_date_raw else ""

    language = getattr(module, "LANGUAGE", "zh")
    if language not in STRINGS:
        language = "zh"

    focus_dur = getattr(module, "FOCUS_DURATION_SECONDS", 0)
    try:
        focus_dur = int(focus_dur)
    except (TypeError, ValueError):
        focus_dur = 0
    focus_dur = max(0, focus_dur)

    focus_start_raw = getattr(module, "FOCUS_STARTED_ISO", "")
    if not isinstance(focus_start_raw, str):
        focus_start_raw = str(focus_start_raw) if focus_start_raw else ""
    focus_started = parse_iso_datetime(focus_start_raw) if focus_start_raw.strip() else None

    countdown_start = parse_iso_datetime(start_raw) if start_raw.strip() else None
    if target_start_date_raw.strip():
        try:
            d0 = datetime.strptime(target_start_date_raw.strip(), "%Y-%m-%d")
            countdown_start = d0.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            pass

    return AppConfig(
        target=parse_iso_datetime(target_raw) if target_raw.strip() else None,
        language=language,
        countdown_mode="day",
        countdown_start=countdown_start,
        alpha=clamp_alpha(getattr(module, "WIDGET_ALPHA", 0.96)),
        focus_duration_seconds=focus_dur,
        focus_started_at=focus_started,
    )


def _migrate_json_if_needed() -> None:
    if CONFIG_PATH.is_file() or not LEGACY_JSON_PATH.is_file():
        return

    try:
        data = json.loads(LEGACY_JSON_PATH.read_text(encoding="utf-8"))
        raw = data.get("target_iso")
        target = parse_iso_datetime(str(raw)) if raw else None
        if target is not None:
            save_config(AppConfig(target, "zh", "day", datetime.now(), 0.96, 0, None))
        LEGACY_JSON_PATH.unlink(missing_ok=True)
    except (OSError, json.JSONDecodeError, ValueError):
        pass


def read_config() -> AppConfig:
    _migrate_json_if_needed()
    if not CONFIG_PATH.is_file():
        return default_config()

    config = _load_config_from_py()
    if config.target is not None and config.countdown_start is None:
        config.countdown_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        save_config(config)
    if config.focus_duration_seconds > 0 and config.focus_started_at is None:
        config = replace(config, focus_duration_seconds=0)
        save_config(config)
        return config
    return _normalize_focus_if_expired(config)


def save_config(config: AppConfig) -> None:
    target_iso = config.target.replace(microsecond=0).isoformat(timespec="seconds") if config.target else ""
    start_iso = (
        config.countdown_start.replace(microsecond=0).isoformat(timespec="seconds")
        if config.countdown_start
        else ""
    )
    target_start_date = config.countdown_start.date().isoformat() if config.countdown_start else ""
    focus_start_iso = (
        config.focus_started_at.replace(microsecond=0).isoformat(timespec="seconds")
        if config.focus_started_at
        else ""
    )
    CONFIG_PATH.write_text(
        "# Time Master — editable local config\n"
        f'LANGUAGE = "{config.language}"\n'
        'COUNTDOWN_MODE = "day"  # "day" | "hour"\n'
        f"WIDGET_ALPHA = {clamp_alpha(config.alpha):.2f}\n"
        f'TARGET_ISO = "{target_iso}"\n'
        f'TARGET_START_ISO = "{target_start_date}"  # YYYY-MM-DD, start of target window\n'
        f'COUNTDOWN_START_ISO = "{start_iso}"\n'
        f"FOCUS_DURATION_SECONDS = {max(0, int(config.focus_duration_seconds))}\n"
        f'FOCUS_STARTED_ISO = "{focus_start_iso}"\n',
        encoding="utf-8",
    )


def _parse_day_entry(raw: Any) -> dict[str, int]:
    if isinstance(raw, dict):
        sec = raw.get("seconds", raw.get("s", 0))
        cnt = raw.get("count", raw.get("c", 0))
        try:
            sec = int(sec)
        except (TypeError, ValueError):
            sec = 0
        try:
            cnt = int(cnt)
        except (TypeError, ValueError):
            cnt = 0
        return {"seconds": max(0, sec), "count": max(0, cnt)}
    if isinstance(raw, (int, float)):
        return {"seconds": max(0, int(raw)), "count": 0}
    return {"seconds": 0, "count": 0}


def load_focus_stats() -> dict[str, dict[str, int]]:
    if not FOCUS_STATS_PATH.is_file():
        return {}
    try:
        data = json.loads(FOCUS_STATS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict[str, int]] = {}
    for k, v in data.items():
        if not isinstance(k, str):
            continue
        out[k] = _parse_day_entry(v)
    return out


def _save_focus_stats(data: dict[str, dict[str, int]]) -> None:
    FOCUS_STATS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_focus_completion(duration_seconds: int, day: datetime | None = None) -> None:
    if duration_seconds <= 0:
        return
    d = (day or datetime.now()).date().isoformat()
    data = load_focus_stats()
    cur = data.get(d, {"seconds": 0, "count": 0})
    cur["seconds"] = cur.get("seconds", 0) + int(duration_seconds)
    cur["count"] = cur.get("count", 0) + 1
    data[d] = cur
    _save_focus_stats(data)


def day_stats_for(stats: dict[str, dict[str, int]], day_iso: str) -> dict[str, int]:
    return stats.get(day_iso, {"seconds": 0, "count": 0})
