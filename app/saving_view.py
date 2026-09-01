from pathlib import Path

from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QKeyEvent
from device import FileSaving
from config import STYLESHEET

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
        self.setStyleSheet(STYLESHEET)


    # builders - make a widget and add it to the layout (run once)
    def buildScreen(self) -> None:
        """Runs the builders in display order."""
        self.buildCounter()
        self.buildCard()
        self.buildToast()
        self.buildFooter()
        self.buildSkipButton()
        self.buildKeepButton()


    def buildCounter(self) -> None:
        """Creates self.counterLabel, the "12 kept, 38 to go" line."""
        self.filesRemaining = QLabel(f"You have backed up {len(self.saving.toBackup)} out of {len(self.saving.deviceFileContent)} files.")
        self.layout.addWidget(self.filesRemaining)


    def buildCard(self) -> None: ################################################################################################
        """Creates self.card, the panel the current file is previewed in."""
        self.card = QLabel()
        self.card.setObjectName("card")
        self.card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.card, stretch=1)


    def buildToast(self) -> None:
        """Creates self.toast, the drop-down banner. Starts hidden."""
        self.toast = QLabel()
        self.toast.setObjectName("toast")
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.hide()
        self.layout.addWidget(self.toast)


    def buildFooter(self) -> None:
        """Creates self.footerRow, the row the two buttons sit in."""
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.layout.addLayout(self.footerRow)


    def buildSkipButton(self) -> None:
        """Creates the left button, wired to onSkipClicked."""
        self.skipButton = QPushButton("Skip")
        self.skipButton.setObjectName("skipButton")
        self.footerRow.addWidget(self.skipButton)
        self.skipButton.clicked.connect(self.onSkipClicked)


    def buildKeepButton(self) -> None:
        """Creates the right button, wired to onKeepClicked."""
        self.keepButton = QPushButton("Keep")
        self.keepButton.setObjectName("confirmButton")
        self.footerRow.addWidget(self.keepButton)
        self.keepButton.clicked.connect(self.onKeepClicked)


    # handlers - respond to a click (run every time the user acts)
    def onKeepClicked(self) -> None:
        """Appends currentFile() to self.approved, toasts, then advances."""
        fileName = self.currentFile()
        if fileName is None:
            return # Normally dont want to return nothing but this seems fair with how self.currentFile() is
        self.approved.append(fileName)
        self.showToast(f"Kept {fileName}")
        self.advance()


    def onSkipClicked(self) -> None:
        """Drops currentFile() and advances."""
        fileName = self.currentFile()
        if fileName is None:
            return # Normally dont want to return nothing but this seems fair with how self.currentFile() is
        self.showToast(f"Skipped {fileName}")
        self.advance()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Maps the left and right arrow keys onto the two buttons."""
        if event.key() == Qt.Key.Key_Left:
            self.onSkipClicked()
        elif event.key() == Qt.Key.Key_Right:
            self.onKeepClicked()
        else:
            super().keyPressEvent(event)


    def onReviewFinished(self) -> None:
        """Runs once the deck is empty - commits the keepers and emits reviewFinished."""
        self.commitToBackup()
        self.updateCounter()
        self.showCard()
        self.skipButton.setEnabled(False)
        self.keepButton.setEnabled(False)
        self.reviewFinished.emit()


    # shared - the work both of the above lean on
    def startBackup(self, path: str) -> None:
        """Loads the deduped files for path and draws the first card. The PC
        destination is expected to already be set on self.saving.local by the
        Destination screen before this runs."""
        self.skipButton.setEnabled(True)
        self.keepButton.setEnabled(True)
        self.saving.loadDeviceFolderContent(path)
        self.saving.local.loadPCFolderContent()
        self.saving.buildBackupList()
        self.loadQueue()
        self.updateCounter()
        self.showCard()


    def loadQueue(self) -> None:
        """Copies self.saving.toBackup into self.queue and resets self.index."""
        self.queue = list(self.saving.toBackup)
        self.approved = []
        self.index = 0


    def currentFile(self) -> str | None:
        """The file on the card now, or None once the deck is empty."""
        if self.index < len(self.queue):
            return self.queue[self.index]
        return None


    def advance(self) -> None:
        """Steps to the next file and redraws, or finishes if there is none."""
        self.index += 1
        if self.currentFile() is None:
            self.onReviewFinished()
        else:
            self.updateCounter()
            self.showCard()


    def showCard(self) -> None: ################################################################################################
        """Draws currentFile() into self.card"""
        fileName = self.currentFile()
        self.card.setText(fileName if fileName is not None else "All files reviewed.")


    def cachePreview(self, fileName: str) -> Path | None: ################################################################################################
        """Pulls fileName to a local temp copy so it can be previewed."""
        pass


    def showToast(self, message: str) -> None:
        """Drops the banner down with message, then hides it again."""
        self.toast.setText(message)
        self.toast.show()
        QTimer.singleShot(1200, self.toast.hide)


    def updateCounter(self) -> None:
        """Refreshes self.counterLabel from approvedCount() and mediaRemaining()."""
        self.filesRemaining.setText(f"{self.approvedCount()} kept, {self.mediaRemaining()} to go")


    def approvedCount(self) -> int:
        """How many files the user has kept so far."""
        return len(self.approved)


    def mediaRemaining(self) -> int:
        """Returns the number of files still to be reviewed."""
        return max(len(self.queue) - self.index, 0)


    def commitToBackup(self) -> None:
        """Replaces self.saving.toBackup with self.approved, so saveAll only pulls the keepers."""
        self.saving.toBackup = list(self.approved)


    @staticmethod
    def formatProgress(transferred: int, total: int) -> str:
        """Turns raw byte counts into a line to put on screen, e.g. "12.8 MB of 240 MB".
        Takes its numbers as arguments so it stays testable without a device attached."""
        def toMB(value: int) -> str:
            return f"{value / (1024 * 1024):.1f} MB"
        return f"{toMB(transferred)} of {toMB(total)}"
