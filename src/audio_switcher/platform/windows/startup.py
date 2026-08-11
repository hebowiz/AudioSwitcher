"""Current-user Windows startup registration."""

from __future__ import annotations

import subprocess
import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "AudioSwitcher"


def startup_command() -> str:
    """Build a command that starts this GUI without requiring a console window."""
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([str(Path(sys.executable).resolve())])

    launcher = Path(sys.argv[0]).resolve()
    if launcher.suffix.casefold() == ".exe" and launcher.stem.casefold() in {
        "audio-switcher",
        "audio_switcher",
    }:
        return subprocess.list2cmdline([str(launcher)])

    python = Path(sys.executable).resolve()
    pythonw = python.with_name("pythonw.exe")
    executable = pythonw if pythonw.exists() else python
    return subprocess.list2cmdline([str(executable), "-m", "audio_switcher"])


class WindowsStartupRegistration:
    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_QUERY_VALUE,
            ) as key:
                value, _value_type = winreg.QueryValueEx(key, VALUE_NAME)
                return bool(value)
        except FileNotFoundError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self._enable()
        else:
            self._disable()

    def _enable(self) -> None:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, startup_command())

    def _disable(self) -> None:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass
