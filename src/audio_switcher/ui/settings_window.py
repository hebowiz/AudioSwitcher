"""Application and system-default target settings window."""

from __future__ import annotations

from collections.abc import Callable

from PySide6 import QtCore, QtGui, QtWidgets

from audio_switcher.domain.models import (
    AppSettings,
    AudioDevice,
    Hotkey,
    SwitchTarget,
    TargetKind,
)
from audio_switcher.platform.windows.audio_sessions import RunningAudioApplication
from audio_switcher.platform.windows.global_hotkeys import HotkeyError, parse_hotkey
from audio_switcher.platform.windows.processes import executable_display_name
from audio_switcher.services.device_matching import resolve_device, resolve_devices


class RefreshComboBox(QtWidgets.QComboBox):
    about_to_show_popup = QtCore.Signal()

    def showPopup(self) -> None:
        self.about_to_show_popup.emit()
        super().showPopup()


class DeviceSelectionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        devices: list[AudioDevice],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("出力デバイスを追加")
        self.resize(420, 280)
        self.selected_device: AudioDevice | None = None
        self._devices = QtWidgets.QListWidget()
        for device in devices:
            item = QtWidgets.QListWidgetItem(device.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, device.to_dict())
            self._devices.addItem(item)
        if self._devices.count():
            self._devices.setCurrentRow(0)
        self._devices.itemDoubleClicked.connect(lambda: self._choose())

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._choose)
        buttons.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("追加する出力デバイス"))
        layout.addWidget(self._devices)
        layout.addWidget(buttons)

    def _choose(self) -> None:
        item = self._devices.currentItem()
        if item is None:
            return
        self.selected_device = AudioDevice.from_dict(item.data(QtCore.Qt.ItemDataRole.UserRole))
        self.accept()


class TargetDialog(QtWidgets.QDialog):
    def __init__(
        self,
        kind: TargetKind,
        active_devices: list[AudioDevice],
        list_applications: Callable[[], list[RunningAudioApplication]],
        target: SwitchTarget | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._kind = kind
        self._active_devices = active_devices
        self._list_applications = list_applications
        self._original = target
        self.result_target: SwitchTarget | None = None
        self.setWindowTitle("切替設定")
        self.resize(560, 430)

        self._name = QtWidgets.QLineEdit()
        self._application = RefreshComboBox()
        self._application.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._application.setMinimumContentsLength(28)
        self._application.currentIndexChanged.connect(self._application_changed)
        self._application.about_to_show_popup.connect(self._refresh_applications)

        self._hotkey = QtWidgets.QKeySequenceEdit()
        self._hotkey.setClearButtonEnabled(True)
        self._devices = QtWidgets.QListWidget()
        self._devices.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        add_device = QtWidgets.QPushButton("追加")
        remove_device = QtWidgets.QPushButton("削除")
        move_up = QtWidgets.QPushButton("上へ")
        move_down = QtWidgets.QPushButton("下へ")
        add_device.clicked.connect(self._add_device)
        remove_device.clicked.connect(self._remove_device)
        move_up.clicked.connect(lambda: self._move_device(-1))
        move_down.clicked.connect(lambda: self._move_device(1))
        device_buttons = QtWidgets.QHBoxLayout()
        device_buttons.addWidget(add_device)
        device_buttons.addWidget(remove_device)
        device_buttons.addStretch(1)
        device_buttons.addWidget(move_up)
        device_buttons.addWidget(move_down)

        form = QtWidgets.QFormLayout()
        form.addRow("表示名", self._name)
        if kind is TargetKind.APPLICATION:
            form.addRow("動作中のアプリ", self._application)
        form.addRow("ショートカット", self._hotkey)

        buttons = QtWidgets.QDialogButtonBox()
        save_button = buttons.addButton("保存", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button = buttons.addButton(
            "キャンセル", QtWidgets.QDialogButtonBox.ButtonRole.RejectRole
        )
        save_button.clicked.connect(self._save_and_close)
        cancel_button.clicked.connect(self.reject)
        save_button.setObjectName("saveTargetButton")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QtWidgets.QLabel("切替順（上から順）"))
        layout.addWidget(self._devices, 1)
        layout.addLayout(device_buttons)
        layout.addWidget(buttons)

        if target is not None:
            self._name.setText(target.name)
            self._hotkey.setKeySequence(QtGui.QKeySequence(target.hotkey.sequence))
            for device in target.devices:
                self._append_device(device)
        elif kind is TargetKind.SYSTEM_DEFAULT:
            self._name.setText("Windows全体")
        if kind is TargetKind.APPLICATION:
            self._refresh_applications(target.executable_path if target else None)

    def _refresh_applications(self, selected_path: str | None = None) -> None:
        if selected_path is None:
            selected_path = self._application.currentData()
        try:
            applications = self._list_applications()
        except Exception as error:  # noqa: BLE001 - Core Audio can return varied COM failures
            QtWidgets.QMessageBox.warning(
                self, "動作中のアプリ", f"Audio Sessionを取得できません。\n{error}"
            )
            return

        self._application.blockSignals(True)
        self._application.clear()
        selected_index = -1
        for application in applications:
            self._application.addItem(
                f"{application.name}  —  {application.executable_path}",
                application.executable_path,
            )
            if selected_path and application.executable_path.casefold() == selected_path.casefold():
                selected_index = self._application.count() - 1
        if selected_path and selected_index < 0:
            self._application.addItem(
                f"{executable_display_name(selected_path)}（現在Audio Sessionなし）"
                f"  —  {selected_path}",
                selected_path,
            )
            selected_index = self._application.count() - 1
        if selected_index >= 0:
            self._application.setCurrentIndex(selected_index)
        self._application.blockSignals(False)
        self._application_changed(self._application.currentIndex())

    def _application_changed(self, index: int) -> None:
        if index < 0 or self._original is not None:
            return
        path = self._application.itemData(index)
        if path:
            self._name.setText(executable_display_name(path))

    def _append_device(self, device: AudioDevice) -> None:
        resolved = resolve_device(device, self._active_devices)
        displayed = resolved or device
        suffix = "" if resolved is not None else "（未接続）"
        item = QtWidgets.QListWidgetItem(f"{displayed.name}{suffix}")
        # Saving the dialog migrates a stale endpoint ID to the currently active one.
        item.setData(QtCore.Qt.ItemDataRole.UserRole, displayed.to_dict())
        self._devices.addItem(item)

    def _configured_devices(self) -> list[AudioDevice]:
        devices: list[AudioDevice] = []
        for index in range(self._devices.count()):
            value = self._devices.item(index).data(QtCore.Qt.ItemDataRole.UserRole)
            devices.append(AudioDevice.from_dict(value))
        return devices

    def _add_device(self) -> None:
        configured_ids = {
            device.id.casefold()
            for device in resolve_devices(self._configured_devices(), self._active_devices)
        }
        choices = [
            device for device in self._active_devices if device.id.casefold() not in configured_ids
        ]
        if not choices:
            QtWidgets.QMessageBox.information(
                self, "出力デバイス", "追加できるデバイスがありません。"
            )
            return
        dialog = DeviceSelectionDialog(choices, self)
        if dialog.exec() and dialog.selected_device is not None:
            self._append_device(dialog.selected_device)

    def _remove_device(self) -> None:
        row = self._devices.currentRow()
        if row >= 0:
            self._devices.takeItem(row)

    def _move_device(self, offset: int) -> None:
        row = self._devices.currentRow()
        destination = row + offset
        if row < 0 or not 0 <= destination < self._devices.count():
            return
        item = self._devices.takeItem(row)
        self._devices.insertItem(destination, item)
        self._devices.setCurrentRow(destination)

    def _save_and_close(self) -> None:
        sequence = self._hotkey.keySequence().toString(
            QtGui.QKeySequence.SequenceFormat.PortableText
        )
        try:
            parse_hotkey(sequence)
            target = SwitchTarget(
                id=self._original.id if self._original else "",
                kind=self._kind,
                name=self._name.text(),
                executable_path=(
                    self._application.currentData()
                    if self._kind is TargetKind.APPLICATION
                    else None
                ),
                hotkey=Hotkey(sequence),
                devices=self._configured_devices(),
            )
            if not target.id:
                # Let the model create an id while preserving validation above.
                target = SwitchTarget(
                    kind=target.kind,
                    name=target.name,
                    executable_path=target.executable_path,
                    hotkey=target.hotkey,
                    devices=target.devices,
                )
        except (ValueError, HotkeyError) as error:
            QtWidgets.QMessageBox.warning(self, "設定を確認してください", str(error))
            return
        self.result_target = target
        super().accept()


class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        settings: AppSettings,
        list_devices: Callable[[], list[AudioDevice]],
        list_applications: Callable[[], list[RunningAudioApplication]],
        save_settings: Callable[[AppSettings], None],
        startup_enabled: Callable[[], bool],
        set_startup_enabled: Callable[[bool], None],
    ) -> None:
        super().__init__()
        self._settings = settings
        self._list_devices = list_devices
        self._list_applications = list_applications
        self._save_settings = save_settings
        self._set_startup_enabled = set_startup_enabled
        self.setWindowTitle("AudioSwitcher 設定")
        self.resize(800, 460)
        status_bar = QtWidgets.QStatusBar(self)
        status_bar.setSizeGripEnabled(False)
        status_bar.setFixedHeight(max(24, status_bar.sizeHint().height()))
        self.setStatusBar(status_bar)
        status_bar.show()

        self._table = QtWidgets.QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["種類", "対象", "ショートカット", "切替順"])
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._table.doubleClicked.connect(self._edit_selected)

        add_app = QtWidgets.QPushButton("アプリを追加")
        self._add_system = QtWidgets.QPushButton("Windows全体を追加")
        edit = QtWidgets.QPushButton("編集")
        remove = QtWidgets.QPushButton("削除")
        save = QtWidgets.QPushButton("保存")
        add_app.clicked.connect(lambda: self._add_target(TargetKind.APPLICATION))
        self._add_system.clicked.connect(lambda: self._add_target(TargetKind.SYSTEM_DEFAULT))
        edit.clicked.connect(self._edit_selected)
        remove.clicked.connect(self._remove_selected)
        save.clicked.connect(self._save)

        self._startup = QtWidgets.QCheckBox("Windowsログイン時に自動起動")
        self._startup.setObjectName("startupCheckBox")
        try:
            self._startup.setChecked(startup_enabled())
        except OSError as error:
            self._startup.setEnabled(False)
            self._startup.setToolTip(f"スタートアップ状態を取得できません: {error}")
        self._startup.toggled.connect(self._change_startup)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(add_app)
        button_row.addWidget(self._add_system)
        button_row.addWidget(edit)
        button_row.addWidget(remove)
        button_row.addStretch(1)
        button_row.addWidget(save)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(self._table)
        layout.addWidget(self._startup)
        layout.addLayout(button_row)
        self.setCentralWidget(central)
        self._refresh()

    def replace_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        self._refresh()

    def _refresh(self) -> None:
        self._table.setRowCount(len(self._settings.targets))
        for row, target in enumerate(self._settings.targets):
            values = (
                "アプリ" if target.kind is TargetKind.APPLICATION else "システム",
                target.display_name,
                target.hotkey.sequence,
                " → ".join(device.name for device in target.devices),
            )
            for column, value in enumerate(values):
                self._table.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        has_system = any(
            target.kind is TargetKind.SYSTEM_DEFAULT for target in self._settings.targets
        )
        self._add_system.setEnabled(not has_system)

    def _devices_or_error(self) -> list[AudioDevice] | None:
        try:
            return self._list_devices()
        except Exception as error:  # noqa: BLE001 - device APIs expose varied COM failures
            QtWidgets.QMessageBox.critical(
                self, "出力デバイス", f"出力デバイスを取得できません。\n{error}"
            )
            return None

    def _add_target(self, kind: TargetKind) -> None:
        devices = self._devices_or_error()
        if devices is None:
            return
        dialog = TargetDialog(kind, devices, self._list_applications, parent=self)
        if dialog.exec() and dialog.result_target is not None:
            self._settings.targets.append(dialog.result_target)
            self._refresh()

    def _selected_row(self) -> int:
        rows = self._table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _edit_selected(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        devices = self._devices_or_error()
        if devices is None:
            return
        target = self._settings.targets[row]
        dialog = TargetDialog(
            target.kind,
            devices,
            self._list_applications,
            target=target,
            parent=self,
        )
        if dialog.exec() and dialog.result_target is not None:
            self._settings.targets[row] = dialog.result_target
            self._refresh()

    def _remove_selected(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        target = self._settings.targets[row]
        answer = QtWidgets.QMessageBox.question(
            self, "設定を削除", f"「{target.display_name}」を削除しますか？"
        )
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            self._settings.targets.pop(row)
            self._refresh()

    def _save(self) -> None:
        try:
            validated = AppSettings(
                version=self._settings.version,
                targets=list(self._settings.targets),
            )
            self._save_settings(validated)
        except Exception as error:  # noqa: BLE001 - present any persistence/hotkey failure
            QtWidgets.QMessageBox.warning(self, "保存できません", str(error))
            return
        self._settings = validated
        self.statusBar().showMessage("設定を保存しました。", 2500)

    def _change_startup(self, enabled: bool) -> None:
        try:
            self._set_startup_enabled(enabled)
        except OSError as error:
            self._startup.blockSignals(True)
            self._startup.setChecked(not enabled)
            self._startup.blockSignals(False)
            QtWidgets.QMessageBox.warning(
                self,
                "スタートアップ登録",
                f"スタートアップ設定を変更できません。\n{error}",
            )
            return
        message = "自動起動を有効にしました。" if enabled else "自動起動を無効にしました。"
        self.statusBar().showMessage(message, 2500)

    def show_and_activate(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
