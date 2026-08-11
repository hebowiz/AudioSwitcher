from pathlib import Path

import pytest

from audio_switcher.domain.models import (
    AppSettings,
    AudioDevice,
    Hotkey,
    SwitchTarget,
    TargetKind,
)
from audio_switcher.storage.json_settings import JsonSettingsStore


def test_save_and_load(tmp_path: Path) -> None:
    store = JsonSettingsStore(tmp_path / "nested" / "config.json")
    settings = AppSettings(
        targets=[
            SwitchTarget(
                kind=TargetKind.SYSTEM_DEFAULT,
                name="Windows全体",
                hotkey=Hotkey("Ctrl+Alt+F12"),
                devices=[AudioDevice("a", "A"), AudioDevice("b", "B")],
            )
        ]
    )

    store.save(settings)

    assert store.load().to_dict() == settings.to_dict()
    assert not (tmp_path / "nested" / "config.json.tmp").exists()


def test_missing_file_returns_empty_settings(tmp_path: Path) -> None:
    settings = JsonSettingsStore(tmp_path / "missing.json").load()

    assert settings.targets == []


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="読み込めません"):
        JsonSettingsStore(path).load()
