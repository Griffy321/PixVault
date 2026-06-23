from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QIcon

from app.card_item import CardStackView, generate_cards
from app.drawer_widget import DrawerWidget


class _ActionButton(QPushButton):
    def __init__(self, symbol, bg, hover_bg, parent=None):
        super().__init__(symbol, parent)
        self._bg = bg
        self._hover = hover_bg
        self.setFixedSize(72, 72)
        self.setFont(QFont("Segoe UI", 26))
        self._apply_style(self._bg)

    def _apply_style(self, bg):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 36px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self._hover};
            }}
            QPushButton:pressed {{
                background-color: {self._hover};
                padding-top: 2px;
            }}
        """)


class SwipeView(QWidget):
    done_selecting = Signal(list)  # emits list of backed-up card dicts

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = generate_cards(50)
        self._backed_up = []
        self._skipped = []
        self._setup_ui()
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------ UI setup

    def _setup_ui(self):
        self.setStyleSheet("background-color: #13131f;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Main area (everything except the drawer)
        main_area = QWidget()
        main_area.setStyleSheet("background: transparent;")
        main_v = QVBoxLayout(main_area)
        main_v.setContentsMargins(20, 20, 20, 20)
        main_v.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout()
        title = QLabel("PixVault")
        title.setStyleSheet("color: #ffffff; font: 700 22px 'Segoe UI';")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self._drawer_btn = QPushButton("☰  Queue")
        self._drawer_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a40;
                color: #a0a0c0;
                border: 1px solid #383858;
                border-radius: 8px;
                padding: 6px 14px;
                font: 13px 'Segoe UI';
            }
            QPushButton:hover { background: #35355a; color: #ffffff; }
        """)
        self._drawer_btn.clicked.connect(self._toggle_drawer)
        top_bar.addWidget(self._drawer_btn)
        main_v.addLayout(top_bar)
        main_v.addSpacing(16)

        # Counter label
        self._counter = QLabel()
        self._counter.setAlignment(Qt.AlignCenter)
        self._counter.setStyleSheet("color: #6060a0; font: 12px 'Segoe UI';")
        main_v.addWidget(self._counter)
        main_v.addSpacing(8)

        # Card + side buttons row
        card_row = QHBoxLayout()
        card_row.setSpacing(24)

        self._skip_btn = _ActionButton("✕", "#3a1a1a", "#c0392b")
        self._skip_btn.clicked.connect(self._on_skip)
        self._skip_btn.setToolTip("Skip  [←]")

        self._stack_view = CardStackView(self._cards)
        self._stack_view.setFixedSize(360, 500)
        self._stack_view.card_dismissed.connect(self._on_card_dismissed)
        self._stack_view.drag_ratio_changed.connect(self._on_drag_ratio)
        self._stack_view.deck_empty.connect(self._on_deck_empty)

        self._save_btn = _ActionButton("♥", "#0d2a1a", "#27ae60")
        self._save_btn.clicked.connect(self._on_backup)
        self._save_btn.setToolTip("Back up  [→]")

        card_row.addStretch()
        card_row.addWidget(self._skip_btn, 0, Qt.AlignVCenter)
        card_row.addWidget(self._stack_view, 0, Qt.AlignVCenter)
        card_row.addWidget(self._save_btn, 0, Qt.AlignVCenter)
        card_row.addStretch()
        main_v.addLayout(card_row)
        main_v.addSpacing(24)

        # Done button
        self._done_btn = QPushButton("Done Selecting  →")
        self._done_btn.setFixedSize(220, 48)
        self._done_btn.setStyleSheet("""
            QPushButton {
                background: #5a3ef5;
                color: white;
                border-radius: 24px;
                font: 700 14px 'Segoe UI';
                border: none;
            }
            QPushButton:hover { background: #7b61ff; }
            QPushButton:pressed { background: #4930d4; padding-top: 2px; }
        """)
        self._done_btn.clicked.connect(self._on_done)

        done_row = QHBoxLayout()
        done_row.addStretch()
        done_row.addWidget(self._done_btn)
        done_row.addStretch()
        main_v.addLayout(done_row)
        main_v.addStretch()

        root.addWidget(main_area, 1)

        # Drawer
        self._drawer = DrawerWidget()
        root.addWidget(self._drawer)

        self._update_counter()

    # ------------------------------------------------------------------ slots

    def _on_card_dismissed(self, card_data, to_right):
        if to_right:
            self._backed_up.append(card_data)
            self._drawer.add_backup(card_data)
        else:
            self._skipped.append(card_data)
            self._drawer.add_skip(card_data)
        self._update_counter()

    def _on_drag_ratio(self, ratio):
        # Tint side buttons as user drags
        if ratio > 0.25:
            self._save_btn._apply_style("#27ae60")
        elif ratio < -0.25:
            self._skip_btn._apply_style("#c0392b")
        else:
            self._save_btn._apply_style("#0d2a1a")
            self._skip_btn._apply_style("#3a1a1a")

    def _on_skip(self):
        self._stack_view.swipe_left()

    def _on_backup(self):
        self._stack_view.swipe_right()

    def _on_deck_empty(self):
        self._skip_btn.setEnabled(False)
        self._save_btn.setEnabled(False)

    def _on_done(self):
        self.done_selecting.emit(self._backed_up)

    def _toggle_drawer(self):
        self._drawer.toggle()
        label = "✕  Close" if self._drawer.is_open() else "☰  Queue"
        self._drawer_btn.setText(label)

    def _update_counter(self):
        remaining = self._stack_view.cards_remaining()
        total = len(self._cards)
        done = total - remaining
        self._counter.setText(f"{done} / {total} reviewed  •  {len(self._backed_up)} queued for backup")

    # ------------------------------------------------------------------ keyboard

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            self._on_skip()
        elif key == Qt.Key_Right:
            self._on_backup()
        else:
            super().keyPressEvent(event)
