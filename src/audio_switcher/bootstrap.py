"""Application dependency wiring and startup."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from audio_switcher.domain.models import AppSettings
from audio_switcher.platform.windows.application_audio_policy import (
    WindowsApplicationAudioPolicy,
)
from audio_switcher.platform.windows.audio_endpoints import WindowsAudioEndpoints
from audio_switcher.platform.windows.audio_sessions import AudioSessionResolver
from audio_switcher.platform.windows.default_audio_policy import WindowsDefaultAudioPolicy
from audio_switcher.platform.windows.global_hotkeys import GlobalHotkeyManager
from audio_switcher.platform.windows.startup import WindowsStartupRegistration
from audio_switcher.services.output_switcher import OutputSwitcher, SwitchError
from audio_switcher.storage.json_settings import JsonSettingsStore
from audio_switcher.ui.osd import OutputOsd
from audio_switcher.ui.settings_window import SettingsWindow
from audio_switcher.ui.tray import TrayController

LOGGER = logging.getLogger(__name__)


def application_data_directory() -> Path:
    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "AudioSwitcher"
    return Path.home() / "AppData" / "Roaming" / "AudioSwitcher"


class AudioSwitcherRuntime(QtCore.QObject):
    def __init__(self, application: QtWidgets.QApplication) -> None:
        super().__init__()
        self._application = application
        self._data_directory = application_data_directory()
        self._store = JsonSettingsStore(self._data_directory / "config.json")
        self._startup = WindowsStartupRegistration()
        self._endpoints = WindowsAudioEndpoints()
        sessions = AudioSessionResolver()
        application_policy = WindowsApplicationAudioPolicy(sessions)
        default_policy = WindowsDefaultAudioPolicy()
        self._switcher = OutputSwitcher(self._endpoints, application_policy, default_policy)
        self._settings = self._load_settings()

        self._osd = OutputOsd()
        self._hotkeys = GlobalHotkeyManager(self)
        self._hotkeys.activated.connect(self._on_hotkey)
        application.installNativeEventFilter(self._hotkeys)

        editable_settings = AppSettings.from_dict(self._settings.to_dict())
        self._window = SettingsWindow(
            editable_settings,
            self._endpoints.list_active,
            sessions.list_running_applications,
            self._save_settings,
            self._startup.is_enabled,
            self._startup.set_enabled,
        )
        self._tray = TrayController(self._window.show_and_activate, self.quit)
        self._tray.show()

        try:
            self._hotkeys.register_targets(self._settings.targets)
        except Exception as error:  # noqa: BLE001 - startup must remain recoverable
            self._tray.notify_error(str(error))
            self._window.show_and_activate()

        if not self._settings.targets or not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self._window.show_and_activate()

    def _load_settings(self) -> AppSettings:
        try:
            return self._store.load()
        except ValueError as error:
            QtWidgets.QMessageBox.warning(
                None,
                "AudioSwitcher",
                f"設定を読み込めないため、空の設定で起動します。\n{error}",
            )
            return AppSettings()

    def _save_settings(self, settings: AppSettings) -> None:
        previous = self._settings
        try:
            self._hotkeys.register_targets(settings.targets)
            self._store.save(settings)
        except Exception:
            self._hotkeys.register_targets(previous.targets)
            raise
        self._settings = settings
        self._window.replace_settings(AppSettings.from_dict(settings.to_dict()))

    @QtCore.Slot(str)
    def _on_hotkey(self, target_id: str) -> None:
        target = next(
            (item for item in self._settings.targets if item.id == target_id),
            None,
        )
        if target is None:
            return
        try:
            result = self._switcher.switch(target)
        except SwitchError as error:
            LOGGER.exception("Audio output switch failed for %s", target.display_name)
            self._tray.notify_error(str(error))
            return
        self._osd.show_switch(result.target_name, result.device.name)

    def quit(self) -> None:
        self._hotkeys.unregister_all()
        self._tray.icon.hide()
        self._application.quit()


def run() -> int:
    if sys.platform != "win32":
        raise RuntimeError("AudioSwitcherはWindows 11専用です。")

    data_directory = application_data_directory()
    data_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=data_directory / "audio-switcher.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )

    application = QtWidgets.QApplication(sys.argv)
    application.setApplicationName("AudioSwitcher")
    application.setOrganizationName("hebowiz")
    application.setQuitOnLastWindowClosed(False)
    runtime = AudioSwitcherRuntime(application)
    application.aboutToQuit.connect(runtime._hotkeys.unregister_all)
    return application.exec()
