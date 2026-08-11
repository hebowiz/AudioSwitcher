import pytest

from audio_switcher.platform.windows.global_hotkeys import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    HotkeyError,
    parse_hotkey,
)


def test_parse_function_hotkey() -> None:
    modifiers, virtual_key = parse_hotkey("Ctrl+Alt+F12")

    assert modifiers == MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
    assert virtual_key == 0x7B


def test_parse_hotkey_requires_modifier() -> None:
    with pytest.raises(HotkeyError, match="修飾キー"):
        parse_hotkey("F12")
