"""Short-lived output-switch notification overlay."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class OutputOsd(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            QtCore.Qt.WindowType.ToolTip
            | QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._label = QtWidgets.QLabel()
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "QLabel { background: rgba(30, 30, 30, 225); color: white; "
            "border-radius: 10px; padding: 14px 22px; font-size: 14px; }"
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_switch(self, target_name: str, device_name: str) -> None:
        self._label.setText(f"{target_name}  →  {device_name}")
        self.adjustSize()
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(
                area.center().x() - self.width() // 2,
                area.bottom() - self.height() - 48,
            )
        self.show()
        self.raise_()
        self._timer.start(1100)
