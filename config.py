"""Konfigurasi aplikasi Libris."""
import os
import sys
from pathlib import Path

APP_NAME = "Libris"
APP_VERSION = "0.1.0"


def data_dir() -> Path:
    """Lokasi data pengguna (bukan folder instalasi). Dapat ditimpa via LIBRIS_DATA_DIR."""
    override = os.environ.get("LIBRIS_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
    else:
        base = Path.home() / ".local" / "share" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return data_dir() / "libris.db"


def backup_dir() -> Path:
    p = data_dir() / "backups"
    p.mkdir(parents=True, exist_ok=True)
    return p
