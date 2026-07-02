from __future__ import annotations
from pathlib import Path


def assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "resources" / "assets"


def icons_dir() -> Path:
    return assets_dir() / "icons"


def fonts_dir() -> Path:
    return assets_dir() / "fonts"


def effects_dir() -> Path:
    return assets_dir() / "effects"
