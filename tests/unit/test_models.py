from pathlib import Path

import pytest

from audio_switcher.domain.models import (
    AppSettings,
    AudioDevice,
    Hotkey,
    SwitchTarget,
    TargetKind,
)


def make_target(tmp_path: Path, *, sequence: str = "Ctrl+Alt+F10") -> SwitchTarget:
    executable = tmp_path / "player.exe"
    return SwitchTarget(
        kind=TargetKind.APPLICATION,
        name="Player",
        executable_path=str(executable),
        hotkey=Hotkey(sequence),
        devices=[AudioDevice("a", "A"), AudioDevice("b", "B")],
    )


def test_settings_round_trip(tmp_path: Path) -> None:
    settings = AppSettings(targets=[make_target(tmp_path)])

    restored = AppSettings.from_dict(settings.to_dict())

    assert restored.to_dict() == settings.to_dict()


def test_target_requires_two_devices(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="2つ以上"):
        SwitchTarget(
            kind=TargetKind.APPLICATION,
            name="Player",
            executable_path=str(tmp_path / "player.exe"),
            hotkey=Hotkey("Ctrl+F9"),
            devices=[AudioDevice("a", "A")],
        )


def test_settings_reject_duplicate_hotkeys(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="同じショートカット"):
        AppSettings(
            targets=[
                make_target(tmp_path, sequence="Ctrl+Alt+F10"),
                make_target(tmp_path, sequence="ctrl+alt+f10"),
            ]
        )


def test_system_target_uses_custom_display_name() -> None:
    target = SwitchTarget(
        kind=TargetKind.SYSTEM_DEFAULT,
        name="デスク全体",
        hotkey=Hotkey("Ctrl+Alt+F11"),
        devices=[AudioDevice("a", "A"), AudioDevice("b", "B")],
    )

    assert target.display_name == "デスク全体"
