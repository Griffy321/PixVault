"""
The line chart on the progress screen, climbing towards the backup's total as each file saves.
"""

import math
from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QFont, QFontMetrics, QMouseEvent, QPaintEvent

# the same colours as config/style.py
ACCENT = QColor("#3d7eff")
SURFACE = QColor("#ffffff")
BORDER = QColor("#d2d6dd")
GRID = QColor("#e8eaee")
TEXT = QColor("#1f2430")
TEXT_SECONDARY = QColor("#5a6270")
TEXT_MUTED = QColor("#9aa1ad")


def toMB(value: float) -> str:
    """
    Bytes as a readable size, e.g. "128.4 MB".
    """
    return f"{value / (1024 * 1024):,.1f} MB"


class ProgressChart(QWidget):
    """
    MB saved against files saved. The hollow dot top right is the backup's total and the line climbs towards it by each file's size, so a video jumps and a file that fails leaves a flat step.
    """

    MARGINS = (72, 36, 28, 32) # left, top, right, bottom - room for the tick and dot labels


    def __init__(self):
        super().__init__()
        self.totalBytes = 0
        self.totalFiles = 0
        self.points: list[tuple[str, int, bool, int]] = [] # (fileName, bytes, saved, bytes saved so far)
        self.hoverIndex: int | None = None
        self.targetRect = QRectF()
        self.setMouseTracking(True)
        self.setMinimumHeight(200)


    def reset(self, totalBytes: int, totalFiles: int) -> None:
        """
        Clears the line and moves the target dot for a new backup.
        """
        self.totalBytes = totalBytes
        self.totalFiles = totalFiles
        self.points = []
        self.hoverIndex = None
        self.update()


    def addFile(self, fileName: str, fileBytes: int, saved: bool, soFar: int) -> None:
        """
        Extends the line by one file.
        """
        self.points.append((fileName, fileBytes, saved, soFar))
        self.update()


    # drawing
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.smallFont())
        plot = self.plotArea()
        self.drawCard(painter)
        self.drawGrid(painter, plot)
        self.drawLine(painter, plot)
        self.drawHover(painter, plot)
        self.drawTarget(painter, plot)
        self.drawTip(painter, plot)
        painter.end()


    def drawCard(self, painter: QPainter) -> None:
        """
        The white panel the chart sits on, matching the preview card.
        """
        painter.setPen(QPen(BORDER, 1))
        painter.setBrush(SURFACE)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)


    def drawGrid(self, painter: QPainter, plot: QRectF) -> None:
        """
        Hairline gridlines at clean MB steps, with the file count along the bottom.
        """
        step = self.tickStep()
        value = 0.0
        while value <= self.totalBytes + 1:
            y = self.position(plot, 0, value).y()
            painter.setPen(QPen(BORDER if value == 0 else GRID, 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(TEXT_MUTED)
            painter.drawText(QRectF(0, y - 8, plot.left() - 10, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.tickLabel(value))
            value += step
        below = QRectF(plot.left(), plot.bottom() + 8, plot.width(), 16)
        painter.drawText(below, Qt.AlignmentFlag.AlignLeft, "0")
        painter.drawText(below, Qt.AlignmentFlag.AlignRight, f"{self.totalFiles} file{'' if self.totalFiles == 1 else 's'}")


    def drawLine(self, painter: QPainter, plot: QRectF) -> None:
        """
        The climb so far, with a faint wash underneath it.
        """
        if not self.points:
            return
        line = QPainterPath(self.position(plot, 0, 0))
        for index, point in enumerate(self.points, start=1):
            line.lineTo(self.position(plot, index, point[3]))
        area = QPainterPath(line)
        area.lineTo(self.position(plot, len(self.points), 0))
        area.closeSubpath()
        wash = QColor(ACCENT)
        wash.setAlphaF(0.1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(wash)
        painter.drawPath(area)
        pen = QPen(ACCENT, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line)


    def drawHover(self, painter: QPainter, plot: QRectF) -> None:
        """
        A hairline through the file under the mouse, with a ring on its point.
        """
        if self.hoverIndex is None:
            return
        point = self.position(plot, self.hoverIndex, self.points[self.hoverIndex - 1][3])
        painter.setPen(QPen(BORDER, 1))
        painter.drawLine(QPointF(point.x(), plot.top()), QPointF(point.x(), plot.bottom()))
        painter.setPen(QPen(ACCENT, 2))
        painter.setBrush(SURFACE)
        painter.drawEllipse(point, 4, 4)


    def drawTarget(self, painter: QPainter, plot: QRectF) -> None:
        """
        The hollow dot the line is climbing to, with the total written above it.
        """
        dot = self.position(plot, self.totalFiles, self.totalBytes)
        painter.setPen(QPen(ACCENT, 2))
        painter.setBrush(SURFACE)
        painter.drawEllipse(dot, 5, 5)
        text = toMB(self.totalBytes)
        self.targetRect = self.textRect(text, dot.x() + 5, dot.y() - 10, alignRight=True)
        painter.setPen(TEXT_SECONDARY)
        painter.drawText(self.targetRect, Qt.AlignmentFlag.AlignRight, text)


    def drawTip(self, painter: QPainter, plot: QRectF) -> None:
        """
        The solid dot on the end of the line, labelled with what has saved so far unless that would land on the total.
        """
        soFar = self.points[-1][3] if self.points else 0
        tip = self.position(plot, len(self.points), soFar)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(SURFACE)
        painter.drawEllipse(tip, 6, 6) # the ring keeps it clear of the line underneath
        painter.setBrush(ACCENT)
        painter.drawEllipse(tip, 4, 4)
        text = toMB(soFar)
        rect = self.textRect(text, tip.x() + 10, tip.y() - 8, alignRight=False)
        if rect.right() > plot.right():
            rect = self.textRect(text, tip.x() - 10, tip.y() - 8, alignRight=True)
        if rect.intersects(self.targetRect.adjusted(-8, -8, 8, 8)):
            return # two figures stacked in the corner read as clutter, and the header carries it anyway
        painter.setPen(TEXT)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, text)


    # hover
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Snaps to the nearest saved file and says what it was, so a big jump can be put down to its file.
        """
        plot = self.plotArea()
        position = event.position()
        if not self.points or not plot.adjusted(-8, -8, 8, 8).contains(position):
            self.clearHover()
            return
        step = plot.width() / max(self.totalFiles, 1)
        index = min(max(round((position.x() - plot.left()) / step), 1), len(self.points))
        if index != self.hoverIndex:
            self.hoverIndex = index
            self.update()
        fileName, fileBytes, saved, soFar = self.points[index - 1]
        status = f"{toMB(soFar)} saved so far" if saved else "Not saved"
        QToolTip.showText(event.globalPosition().toPoint(), f"{fileName}\n{toMB(fileBytes)}\n{status}", self)


    def leaveEvent(self, event) -> None:
        self.clearHover()
        super().leaveEvent(event)


    def clearHover(self) -> None:
        if self.hoverIndex is not None:
            self.hoverIndex = None
            self.update()
        QToolTip.hideText()


    # shared
    def plotArea(self) -> QRectF:
        """
        The rectangle the line is drawn in, inside the margins.
        """
        left, top, right, bottom = self.MARGINS
        return QRectF(left, top, self.width() - left - right, self.height() - top - bottom)


    def position(self, plot: QRectF, files: int, savedBytes: float) -> QPointF:
        """
        Where a point sits on screen, files along and bytes up.
        """
        x = plot.left() + plot.width() * files / max(self.totalFiles, 1)
        y = plot.bottom() - plot.height() * savedBytes / max(self.totalBytes, 1)
        return QPointF(x, y)


    def tickStep(self) -> float:
        """
        A clean gap between gridlines in bytes, so the ticks read 0 / 50 / 100 MB rather than 0 / 47.3 / 94.6.
        """
        roughMB = self.totalBytes / (1024 * 1024) / 4
        if roughMB <= 0:
            return float(max(self.totalBytes, 1))
        magnitude = 10 ** math.floor(math.log10(roughMB))
        for nice in (1, 2, 2.5, 5, 10):
            if nice * magnitude >= roughMB:
                return nice * magnitude * 1024 * 1024
        return 10 * magnitude * 1024 * 1024


    def tickLabel(self, value: float) -> str:
        return f"{value / (1024 * 1024):,g} MB"


    def textRect(self, text: str, anchorX: float, bottomY: float, alignRight: bool) -> QRectF:
        """
        The box a label will take up, measured before drawing so it can be moved rather than clipped.
        """
        metrics = QFontMetrics(self.smallFont())
        width = metrics.horizontalAdvance(text) + 2
        left = anchorX - width if alignRight else anchorX
        top = max(bottomY - metrics.height(), 2)
        return QRectF(left, top, width, metrics.height())


    def smallFont(self) -> QFont:
        font = QFont(self.font())
        font.setPixelSize(11)
        return font
