from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

from app.swipe_view import SwipeView
from app.backup_view import BackupView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixVault")
        self.resize(1000, 700)
        self.setMinimumSize(800, 580)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._swipe_view = SwipeView()
        self._backup_view = BackupView()

        self._stack.addWidget(self._swipe_view)
        self._stack.addWidget(self._backup_view)

        self._swipe_view.done_selecting.connect(self._show_backup)
        self._backup_view.back_requested.connect(self._show_swipe)

    def _show_backup(self, backed_up_cards):
        self._backup_view.set_cards(backed_up_cards)
        self._stack.setCurrentWidget(self._backup_view)

    def _show_swipe(self):
        self._stack.setCurrentWidget(self._swipe_view)
        self._swipe_view.setFocus()
