"""System tray integration."""

from __future__ import annotations

from collections.abc import Callable

from PySide6 import QtWidgets

from audio_switcher.ui.icons import tray_icon


class TrayController:
    def __init__(
        self,
        show_settings: Callable[[], None],
        quit_application: Callable[[], None],
    ) -> None:
        self.icon = QtWidgets.QSystemTrayIcon(tray_icon())
        self.icon.setToolTip("AudioSwitcher")
        menu = QtWidgets.QMenu()
        settings_action = menu.addAction("設定を開く")
        settings_action.triggered.connect(show_settings)
        menu.addSeparator()
        quit_action = menu.addAction("終了")
        quit_action.triggered.connect(quit_application)
        self.icon.setContextMenu(menu)
        self.icon.activated.connect(
            lambda reason: (
                show_settings()
                if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick
                else None
            )
        )

    def show(self) -> None:
        self.icon.show()

    def notify_error(self, message: str) -> None:
        self.icon.showMessage(
            "AudioSwitcher",
            message,
            QtWidgets.QSystemTrayIcon.MessageIcon.Warning,
            4000,
        )
