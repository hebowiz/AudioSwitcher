from PySide6 import QtCore, QtGui, QtWidgets

from audio_switcher.domain.models import AppSettings, AudioDevice, TargetKind
from audio_switcher.platform.windows.audio_sessions import RunningAudioApplication
from audio_switcher.ui.settings_window import (
    DeviceSelectionDialog,
    SettingsWindow,
    TargetDialog,
)

DEVICES = [AudioDevice("a", "A"), AudioDevice("b", "B")]


def save_button(dialog: TargetDialog) -> QtWidgets.QPushButton:
    button = dialog.findChild(QtWidgets.QPushButton, "saveTargetButton")
    assert button is not None
    return button


def complete_devices_and_hotkey(dialog: TargetDialog) -> None:
    dialog._hotkey.setKeySequence(QtGui.QKeySequence("Ctrl+Alt+F12"))
    dialog._append_device(DEVICES[0])
    dialog._append_device(DEVICES[1])


def test_system_target_save_closes_dialog(qtbot) -> None:
    dialog = TargetDialog(TargetKind.SYSTEM_DEFAULT, DEVICES, list)
    qtbot.addWidget(dialog)
    complete_devices_and_hotkey(dialog)
    dialog._name.setText("デスク全体")

    qtbot.mouseClick(save_button(dialog), QtCore.Qt.MouseButton.LeftButton)

    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
    assert dialog.result_target is not None
    assert dialog.result_target.kind is TargetKind.SYSTEM_DEFAULT
    assert dialog.result_target.executable_path is None
    assert dialog.result_target.display_name == "デスク全体"


def test_application_is_selected_from_running_audio_sessions(qtbot) -> None:
    applications = [RunningAudioApplication("C:/Apps/player.exe", "Player.exe")]
    dialog = TargetDialog(TargetKind.APPLICATION, DEVICES, lambda: applications)
    qtbot.addWidget(dialog)
    complete_devices_and_hotkey(dialog)

    qtbot.mouseClick(save_button(dialog), QtCore.Qt.MouseButton.LeftButton)

    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
    assert dialog.result_target is not None
    assert dialog.result_target.executable_path.lower().endswith("apps\\player.exe")


def test_application_list_refreshes_when_popup_opens(qtbot) -> None:
    calls = 0

    def applications() -> list[RunningAudioApplication]:
        nonlocal calls
        calls += 1
        return [RunningAudioApplication("C:/Apps/player.exe", "Player.exe")]

    dialog = TargetDialog(TargetKind.APPLICATION, DEVICES, applications)
    qtbot.addWidget(dialog)
    assert calls == 1

    dialog._application.showPopup()
    dialog._application.hidePopup()

    assert calls == 2


def test_device_picker_displays_names_without_ids(qtbot) -> None:
    dialog = DeviceSelectionDialog(DEVICES)
    qtbot.addWidget(dialog)

    displayed = [dialog._devices.item(row).text() for row in range(dialog._devices.count())]

    assert displayed == ["A", "B"]


def test_startup_checkbox_applies_immediately(qtbot) -> None:
    changes: list[bool] = []
    window = SettingsWindow(
        AppSettings(),
        lambda: DEVICES,
        list,
        lambda _settings: None,
        lambda: False,
        changes.append,
    )
    qtbot.addWidget(window)

    window._startup.setChecked(True)

    assert changes == [True]


def test_status_message_space_is_reserved_before_first_message(qtbot) -> None:
    window = SettingsWindow(
        AppSettings(),
        lambda: DEVICES,
        list,
        lambda _settings: None,
        lambda: False,
        lambda _enabled: None,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    before = window.centralWidget().height()

    window.statusBar().showMessage("設定を保存しました。", 2500)
    QtWidgets.QApplication.processEvents()

    assert window.statusBar().height() >= 24
    assert window.centralWidget().height() == before
