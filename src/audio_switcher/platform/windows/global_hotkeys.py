"""Win32 global hotkey registration and Qt message dispatch."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6 import QtCore

from audio_switcher.domain.models import SwitchTarget

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class HotkeyError(RuntimeError):
    pass


_SPECIAL_KEYS = {
    "SPACE": 0x20,
    "TAB": 0x09,
    "BACKTAB": 0x09,
    "BACKSPACE": 0x08,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "RETURN": 0x0D,
    "ENTER": 0x0D,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "PAUSE": 0x13,
    "PRINT": 0x2C,
    "HOME": 0x24,
    "END": 0x23,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "PGUP": 0x21,
    "PGDOWN": 0x22,
}


def parse_hotkey(sequence: str) -> tuple[int, int]:
    parts = [part.strip() for part in sequence.split("+") if part.strip()]
    if len(parts) < 2:
        raise HotkeyError("ショートカットには修飾キーを含めてください。")

    modifiers = 0
    for part in parts[:-1]:
        normalized = part.upper()
        if normalized in {"CTRL", "CONTROL"}:
            modifiers |= MOD_CONTROL
        elif normalized == "ALT":
            modifiers |= MOD_ALT
        elif normalized == "SHIFT":
            modifiers |= MOD_SHIFT
        elif normalized in {"META", "WIN", "WINDOWS"}:
            modifiers |= MOD_WIN
        else:
            raise HotkeyError(f"未対応の修飾キーです: {part}")

    key_name = parts[-1].upper()
    if len(key_name) == 1 and key_name.isascii() and key_name.isalnum():
        virtual_key = ord(key_name)
    elif key_name.startswith("F") and key_name[1:].isdigit():
        function_number = int(key_name[1:])
        if not 1 <= function_number <= 24:
            raise HotkeyError("FキーはF1からF24まで使用できます。")
        virtual_key = 0x70 + function_number - 1
    elif key_name in _SPECIAL_KEYS:
        virtual_key = _SPECIAL_KEYS[key_name]
    else:
        raise HotkeyError(f"未対応のキーです: {parts[-1]}")
    return modifiers | MOD_NOREPEAT, virtual_key


class GlobalHotkeyManager(QtCore.QObject, QtCore.QAbstractNativeEventFilter):
    activated = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        QtCore.QObject.__init__(self, parent)
        QtCore.QAbstractNativeEventFilter.__init__(self)
        self._registered: dict[int, str] = {}
        self._user32 = ctypes.windll.user32

    def register_targets(self, targets: list[SwitchTarget]) -> None:
        self.unregister_all()
        for hotkey_id, target in enumerate(targets, start=1):
            modifiers, virtual_key = parse_hotkey(target.hotkey.sequence)
            if not self._user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
                self.unregister_all()
                raise HotkeyError(f"ショートカットを登録できません: {target.hotkey.sequence}")
            self._registered[hotkey_id] = target.id

    def unregister_all(self) -> None:
        for hotkey_id in tuple(self._registered):
            self._user32.UnregisterHotKey(None, hotkey_id)
        self._registered.clear()

    def nativeEventFilter(self, event_type: QtCore.QByteArray, message: int) -> tuple[bool, int]:
        del event_type
        native_message = MSG.from_address(int(message))
        if native_message.message == WM_HOTKEY:
            target_id = self._registered.get(int(native_message.wParam))
            if target_id is not None:
                self.activated.emit(target_id)
                return True, 0
        return False, 0
