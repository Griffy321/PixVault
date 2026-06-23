from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QBrush


class _CardTile(QWidget):
    def __init__(self, card_data, parent=None):
        super().__init__(parent)
        self.card_data = card_data
        self.setFixedSize(90, 120)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(self.card_data["color"])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        from PySide6.QtCore import QRectF
        painter.drawRoundedRect(
            QRectF(0, 0, self.width(), self.height() * 0.4), 10, 10
        )
        painter.setPen(QColor(255, 255, 255, 220))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(self.rect().adjusted(0, -10, 0, 0), Qt.AlignCenter,
                         f"#{self.card_data['id']}")
        painter.setPen(QColor(255, 255, 255, 140))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(self.rect().adjusted(0, 16, 0, 0), Qt.AlignCenter, "Photo")


class BackupView(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = []
        self.setStyleSheet("background-color: #13131f;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)

        # Header row
        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8080b0;
                border: 1px solid #303050;
                border-radius: 8px;
                padding: 6px 16px;
                font: 13px 'Segoe UI';
            }
            QPushButton:hover { color: #ffffff; border-color: #6060a0; }
        """)
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(28)

        # Title
        self._title = QLabel("Backup Preview")
        self._title.setStyleSheet("color: #ffffff; font: 700 28px 'Segoe UI';")
        layout.addWidget(self._title)
        layout.addSpacing(6)

        self._subtitle = QLabel()
        self._subtitle.setStyleSheet("color: #6060a0; font: 14px 'Segoe UI';")
        layout.addWidget(self._subtitle)
        layout.addSpacing(28)

        # Scroll area with card grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(12)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll, 1)
        layout.addSpacing(28)

        # Empty state label (shown when no cards)
        self._empty_label = QLabel("No photos selected for backup.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #505070; font: 16px 'Segoe UI';")
        layout.addWidget(self._empty_label)

        # Confirm button
        self._confirm_btn = QPushButton("Confirm Backup")
        self._confirm_btn.setFixedSize(220, 52)
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: #0a1f12;
                border-radius: 26px;
                font: 700 15px 'Segoe UI';
                border: none;
            }
            QPushButton:hover { background: #27ae60; }
            QPushButton:pressed { background: #1e8449; padding-top: 2px; }
            QPushButton:disabled { background: #1e3a28; color: #406040; }
        """)
        # Does nothing for now
        self._confirm_btn.clicked.connect(lambda: None)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._confirm_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def set_cards(self, cards):
        self._cards = cards

        # Clear existing grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cards:
            self._subtitle.setText("No photos queued for backup.")
            self._empty_label.show()
            self._confirm_btn.setEnabled(False)
            return

        self._empty_label.hide()
        self._confirm_btn.setEnabled(True)
        n = len(cards)
        self._title.setText("Backup Preview")
        self._subtitle.setText(
            f"{n} photo{'s' if n != 1 else ''} ready to back up"
        )

        cols = 6
        for i, card_data in enumerate(cards):
            tile = _CardTile(card_data)
            self._grid.addWidget(tile, i // cols, i % cols)
