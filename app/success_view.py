from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget
from PySide6.QtCore import Signal, Qt
from device import FileSaving
from config import STYLESHEET
from app.progress_chart import toMB


class SuccessScreen(QWidget):
    """
    The last screen - what was saved and where, anything that was not, and the way out.
    """

    restartRequested = Signal()
    quitRequested = Signal()


    def __init__(self, saving: FileSaving):
        super().__init__()
        self.saving = saving
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(8)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(STYLESHEET)


    # builders - make a widget and add it to the layout (run once)
    def buildScreen(self) -> None:
        """
        Runs the builders in display order.
        """
        self.buildHeader()
        self.buildNotSavedList()
        self.buildFooter()
        self.buildRestartButton()
        self.buildQuitButton()


    def buildHeader(self) -> None:
        """
        Creates the title, the totals, and where the files went.
        """
        self.title = QLabel()
        self.title.setObjectName("title")
        self.summary = QLabel()
        self.destination = QLabel()
        self.destination.setObjectName("pathLabel")
        self.destination.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) # so the path can be copied
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.summary)
        self.layout.addWidget(self.destination)
        self.layout.addSpacing(8)


    def buildNotSavedList(self) -> None:
        """
        Creates self.notSavedList, the files that failed or a cancel never reached. Hidden when there are none.
        """
        self.notSavedLabel = QLabel("These files were not saved:")
        self.notSavedLabel.setObjectName("pathLabel")
        self.notSavedList = QListWidget()
        self.layout.addWidget(self.notSavedLabel)
        self.layout.addWidget(self.notSavedList, stretch=1)
        self.layout.addStretch() # takes the space instead while the list is hidden


    def buildFooter(self) -> None:
        """
        Creates self.footerRow, the row the two buttons sit in.
        """
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.footerRow.addStretch()
        self.layout.addLayout(self.footerRow)


    def buildRestartButton(self) -> None:
        """
        Creates the button back to the navigation screen, wired to restartRequested.
        """
        button = QPushButton("Back Up Another Folder")
        self.footerRow.insertWidget(0, button)      # left of the stretch
        button.clicked.connect(self.restartRequested.emit)


    def buildQuitButton(self) -> None:
        """
        Creates the quit button, wired to quitRequested.
        """
        button = QPushButton("Quit PixVault")
        button.setObjectName("confirmButton")
        self.footerRow.addWidget(button)   # right of the stretch
        button.clicked.connect(self.quitRequested.emit)


    # shared
    def showResults(self, saved: list[str], failed: list[str], notReached: list[str]) -> None:
        """
        Fills the screen in from a finished, or cancelled, backup.
        """
        self.title.setText(self.titleText(saved, failed, notReached))
        if not saved and not failed and not notReached:
            self.summary.setText("You didn't keep any files, so there was nothing to save.")
        else:
            self.summary.setText(f"{len(saved)} file{'' if len(saved) == 1 else 's'} saved, {toMB(self.saving.transferredBytes)}.")
        self.destination.setText(f"Saved to {self.saving.local.pcFiles}" if saved else "")
        self.destination.setVisible(bool(saved))
        self.notSavedList.clear()
        for fileName in failed:
            self.notSavedList.addItem(f"{fileName}   -   failed to save")
        for fileName in notReached:
            self.notSavedList.addItem(f"{fileName}   -   cancelled before it was reached")
        hasProblems = bool(failed or notReached)
        self.notSavedLabel.setVisible(hasProblems)
        self.notSavedList.setVisible(hasProblems)


    def titleText(self, saved: list[str], failed: list[str], notReached: list[str]) -> str:
        """
        The heading, picked by how the backup ended.
        """
        if not saved and not failed and not notReached:
            return "Nothing to back up"
        if notReached:
            return "Backup cancelled"
        if failed:
            return "Backup finished, but some files were not saved"
        return "Backup complete"
