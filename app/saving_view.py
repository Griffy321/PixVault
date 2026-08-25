from pathlib import Path

from PySide6.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout , QHBoxLayout, QLineEdit, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent
from device import FileSaving

class SavingScreen(QWidget):
    """The screen where users can see the deduped files they will want to save.

    One card at a time: right keeps the file for backup, left drops it.
    self.saving.toBackup is the deck to review and is left alone until
    commitToBackup() replaces it with what the user kept.
    """

    reviewFinished = Signal()


    def __init__(self, saving: FileSaving):
        super().__init__()
        self.saving = saving
        self.queue: list[str] = []      # deduped files still to be shown
        self.approved: list[str] = []   # the ones swiped right
        self.index = 0                  # position in self.queue
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("PixVault - Choose a folder")


    # builders - make a widget and add it to the layout (run once)
    def buildScreen(self) -> None:
        """Runs the builders in display order."""
        pass


    def buildCounter(self) -> None:
        """Creates self.counterLabel, the "12 kept, 38 to go" line."""
        pass


    def buildCard(self) -> None:
        """Creates self.card, the panel the current file is previewed in."""
        pass


    def buildToast(self) -> None:
        """Creates self.toast, the drop-down banner. Starts hidden."""
        pass


    def buildFooter(self) -> None:
        """Creates self.footerRow, the row the two buttons sit in."""
        pass


    def buildSkipButton(self) -> None:
        """Creates the red left button, wired to onSkipClicked."""
        pass


    def buildKeepButton(self) -> None:
        """Creates the green right button, wired to onKeepClicked."""
        pass


    # handlers - respond to a click (run every time the user acts)
    def onKeepClicked(self) -> None:
        """Appends currentFile() to self.approved, toasts, then advances."""
        pass


    def onSkipClicked(self) -> None:
        """Drops currentFile() and advances."""
        pass


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Maps the left and right arrow keys onto the two buttons."""
        pass


    def onReviewFinished(self) -> None:
        """Runs once the deck is empty - commits the keepers and emits reviewFinished."""
        pass


    # shared - the work both of the above lean on
    def startBackup(self, path: str) -> None:
        """Loads the deduped files for path and draws the first card."""
        pass


    def loadQueue(self) -> None:
        """Copies self.saving.toBackup into self.queue and resets self.index."""
        pass


    def currentFile(self) -> str | None:
        """The file on the card now, or None once the deck is empty."""
        pass


    def advance(self) -> None:
        """Steps to the next file and redraws, or finishes if there is none."""
        pass


    def showCard(self) -> None:
        """Draws currentFile() into self.card, as a still or a video frame."""
        pass


    def cachePreview(self, fileName: str) -> Path | None:
        """Pulls fileName to a local temp copy so it can be previewed."""
        pass


    def showToast(self, message: str) -> None:
        """Drops the banner down with message, then hides it again."""
        pass


    def updateCounter(self) -> None:
        """Refreshes self.counterLabel from approvedCount() and mediaRemaining()."""
        pass


    def approvedCount(self) -> int:
        """How many files the user has kept so far."""
        pass


    def mediaRemaining(self) -> int:
        """Returns the number of files still to be reviewed."""
        pass


    def commitToBackup(self) -> None:
        """Replaces self.saving.toBackup with self.approved, so saveAll only pulls the keepers."""
        pass


    @staticmethod
    def formatProgress(transferred: int, total: int) -> str:
        """Turns raw byte counts into a line to put on screen, e.g. "12.8 MB of 240 MB".
        Takes its numbers as arguments so it stays testable without a device attached."""
        pass

