from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from .models import DeviceConfig


APP_NAME = "HikvisionSecureViewer"


def settings_path() -> Path:
    root = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
    return root / "device.json"


def save_config(config: DeviceConfig) -> None:
    path = settings_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    path.chmod(0o600)


def load_config() -> DeviceConfig | None:
    path = settings_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DeviceConfig(**payload)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
