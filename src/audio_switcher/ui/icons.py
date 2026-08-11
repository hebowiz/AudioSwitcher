"""Theme-independent application icons drawn at native tray sizes."""

from __future__ import annotations

from PySide6 import QtCore, QtGui


def tray_icon() -> QtGui.QIcon:
    """Return a white speaker with a black outline for light and dark taskbars."""
    icon = QtGui.QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        outline_width = max(1.5, size * 0.09)
        painter.setPen(
            QtGui.QPen(
                QtGui.QColor("#101010"),
                outline_width,
                QtCore.Qt.PenStyle.SolidLine,
                QtCore.Qt.PenCapStyle.RoundCap,
                QtCore.Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setBrush(QtGui.QColor("#FFFFFF"))
        speaker = QtGui.QPolygonF(
            [
                QtCore.QPointF(size * 0.04, size * 0.36),
                QtCore.QPointF(size * 0.27, size * 0.36),
                QtCore.QPointF(size * 0.55, size * 0.09),
                QtCore.QPointF(size * 0.55, size * 0.91),
                QtCore.QPointF(size * 0.27, size * 0.64),
                QtCore.QPointF(size * 0.04, size * 0.64),
            ]
        )
        painter.drawPolygon(speaker)

        wave_rectangle = QtCore.QRectF(
            size * 0.37,
            size * 0.16,
            size * 0.59,
            size * 0.68,
        )
        for color, width in (
            (QtGui.QColor("#101010"), max(2.0, size * 0.13)),
            (QtGui.QColor("#FFFFFF"), max(1.0, size * 0.055)),
        ):
            painter.setPen(
                QtGui.QPen(
                    color,
                    width,
                    QtCore.Qt.PenStyle.SolidLine,
                    QtCore.Qt.PenCapStyle.RoundCap,
                )
            )
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawArc(wave_rectangle, -48 * 16, 96 * 16)

        painter.end()
        icon.addPixmap(pixmap)
    return icon
