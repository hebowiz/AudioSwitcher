"""Atomic JSON settings persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from audio_switcher.domain.models import AppSettings


class JsonSettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise TypeError("設定ファイルのルートはオブジェクトである必要があります。")
            return AppSettings.from_dict(value)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"設定ファイルを読み込めません: {error}") from error

    def save(self, settings: AppSettings) -> None:
        settings.__post_init__()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = json.dumps(settings.to_dict(), ensure_ascii=False, indent=2) + "\n"
        try:
            temporary.write_text(payload, encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
