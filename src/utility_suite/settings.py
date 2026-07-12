"""Small local settings store; no settings are included in the repository."""

from __future__ import annotations

import json
import os
from pathlib import Path


def settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "OfflineUtilitySuite" / "settings.json"


def load_language(app_key: str) -> str:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        language = data.get("languages", {}).get(app_key, "zh")
        return language if language in {"zh", "en"} else "zh"
    except (OSError, ValueError, TypeError):
        return "zh"


def save_language(app_key: str, language: str) -> None:
    path = settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        languages = data.setdefault("languages", {})
        languages[app_key] = language
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
    except (OSError, ValueError, TypeError):
        return
