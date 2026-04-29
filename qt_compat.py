import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent
VENDOR_DIR = _BASE / ".pyside6_vendor"

if VENDOR_DIR.is_dir():
    vendor_path = str(VENDOR_DIR)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)


def resource_root() -> Path:
    """Static files shipped with the app (e.g. assets/). PyInstaller extracts to sys._MEIPASS."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return _BASE


def data_root() -> Path:
    """Writable config and statistics. The .app bundle keeps these outside the read-only bundle."""
    if getattr(sys, "frozen", False):
        p = Path.home() / "Library/Application Support/TimeMaster-Widget"
        p.mkdir(parents=True, exist_ok=True)
        return p
    return _BASE


# Repository / dev tree root (location of this file). Prefer resource_root / data_root for new code.
PROJECT_ROOT = _BASE
