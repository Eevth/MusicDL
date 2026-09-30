"""Simpan pengaturan lokal (folder download, akun GitHub, dll)."""

import json
import os


def settings_path():
    folder = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "MusicDL")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def load_settings():
    path = settings_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(data):
    path = settings_path()
    current = load_settings()
    current.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current
