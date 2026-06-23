from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QBrush


class MiniCard(QFrame):
    def __init__(self, card_data, parent=None):
        super().__init__(parent)
        self.card_data = card_data
        self.setFixedSize(46, 62)
        self.setToolTip(f"Photo #{card_data['id']}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(self.card_data["color"])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)
        painter.setPen(QColor(255, 255, 255, 200))
        from PySide6.QtGui import QFont
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"#{self.card_data['id']}")


class CardPile(QWidget):
    """Wrapping grid of MiniCards under a section header."""

    def __init__(self, title, accent_color, parent=None):
        super().__init__(parent)
        self._cards = []
        self._accent = accent_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(6)

        self._header = QLabel(title)
        self._header.setStyleSheet(f"""
            color: {accent_color};
            font: 700 11px 'Segoe UI';
            padding: 2px 0;
            border-bottom: 1px solid {accent_color}44;
        """)
        layout.addWidget(self._header)

        self._count_label = QLabel("0 photos")
        self._count_label.setStyleSheet("color: #9090b0; font: 10px 'Segoe UI';")
        layout.addWidget(self._count_label)

        self._grid_widget = QWidget()
        self._grid_layout = QHBoxLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(4)
        self._grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self._grid_widget)

        # Use a flow-wrap approach via a simple re-layout widget
        self._flow = _FlowWidget()
        layout.addWidget(self._flow)
        # Remove the hbox grid we just added (using flow instead)
        layout.removeWidget(self._grid_widget)
        self._grid_widget.deleteLater()

    def add_card(self, card_data):
        self._cards.append(card_data)
        mini = MiniCard(card_data)
        self._flow.add_widget(mini)
        n = len(self._cards)
        self._count_label.setText(f"{n} photo{'s' if n != 1 else ''}")

    def clear(self):
        self._cards.clear()
        self._flow.clear_widgets()
        self._count_label.setText("0 photos")


class _FlowWidget(QWidget):
    """Simple flow layout widget (wraps children left-to-right)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets = []

    def add_widget(self, w):
        w.setParent(self)
        self._widgets.append(w)
        self._relayout()
        self.updateGeometry()

    def clear_widgets(self):
        for w in self._widgets:
            w.deleteLater()
        self._widgets.clear()
        self.setFixedHeight(0)

    def _relayout(self):
        cols = 3
        gap = 4
        w, h = 46, 62
        for i, widget in enumerate(self._widgets):
            col = i % cols
            row = i // cols
            widget.move(col * (w + gap), row * (h + gap))
            widget.show()
        rows = (len(self._widgets) + cols - 1) // cols if self._widgets else 0
        self.setFixedHeight(max(0, rows * (h + gap)))

    def sizeHint(self):
        from PySide6.QtCore import QSize
        cols = 3
        gap = 4
        rows = (len(self._widgets) + cols - 1) // cols if self._widgets else 0
        return QSize(3 * (46 + gap), rows * (62 + gap))


class DrawerWidget(QWidget):
    """Collapsible right-side panel showing backed-up and skipped cards."""

    DRAWER_W = 200
    COLLAPSED_W = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._open = False
        self.setFixedWidth(self.COLLAPSED_W)
        self.setStyleSheet("background-color: #1e1e30; border-left: 1px solid #303050;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 16, 12, 16)
        outer.setSpacing(16)

        title = QLabel("Queue")
        title.setStyleSheet("color: #ffffff; font: 700 14px 'Segoe UI';")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        self._backup_pile = CardPile("To Back Up", "#2ECC71")
        self._skip_pile = CardPile("Skipped", "#E74C3C")
        inner_layout.addWidget(self._backup_pile)
        inner_layout.addWidget(self._skip_pile)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(260)
        self._anim_max.setEasingCurve(QEasingCurve.OutCubic)

    def toggle(self):
        self._open = not self._open
        target = self.DRAWER_W if self._open else self.COLLAPSED_W
        for anim in (self._anim, self._anim_max):
            anim.stop()
            anim.setStartValue(self.width())
            anim.setEndValue(target)
            anim.start()

    def is_open(self):
        return self._open

    def add_backup(self, card_data):
        self._backup_pile.add_card(card_data)

    def add_skip(self, card_data):
        self._skip_pile.add_card(card_data)

    def reset(self):
        self._backup_pile.clear()
        self._skip_pile.clear()
