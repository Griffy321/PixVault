from PySide6.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QMessageBox
)
from PySide6.QtCore import Signal
from local import LocalFolder
from config import BACKUP_DESTINATION, STYLESHEET


class DestinationScreen(QWidget):
    """
    The screen for picking where on this PC backed up files get saved. Shows a text field the user types a folder path into, and confirms it before moving onto saving.
    """

    destinationConfirmed = Signal()
    backRequested = Signal()


    def __init__(self, local: LocalFolder):
        super().__init__()
        self.local = local
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("PixVault - Choose a destination")
        self.setStyleSheet(STYLESHEET)


    # builders - make a widget and add it to the layout (run once)
    def buildScreen(self) -> None:
        """
        Runs the builders in display order.
        """
        self.buildInstructions()
        self.buildPathInput()
        self.buildFooter()
        self.buildBack()
        self.buildConfirm()


    def buildInstructions(self) -> None:
        """
        Creates the label explaining what to type in the field below.
        """
        label = QLabel("Where on this PC should backed up files be saved?")
        label.setObjectName("pathLabel")
        self.layout.addWidget(label)


    def buildPathInput(self) -> None:
        """
        Creates self.pathInput, the folder path field, and a button that fills it with the recommended default path.
        """
        row = QHBoxLayout()
        row.setSpacing(8)
        self.pathInput = QLineEdit()
        self.pathInput.setPlaceholderText(r"e.g. C:\Users\you\Pictures\PixVault Backup")
        self.pathInput.returnPressed.connect(self.onConfirmClicked)
        defaultButton = QPushButton("Use Default Path")
        row.addWidget(self.pathInput)
        row.addWidget(defaultButton)
        self.layout.addLayout(row)
        self.layout.addStretch()
        defaultButton.clicked.connect(self.onUseDefaultClicked)


    def buildFooter(self) -> None:
        """
        Creates self.footerRow, the row the two buttons sit in.
        """
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.footerRow.addStretch()
        self.layout.addLayout(self.footerRow)


    def buildBack(self) -> None:
        """
        Creates the back button, wired to backRequested.
        """
        button = QPushButton("Go Back")
        self.footerRow.insertWidget(0, button)      # left of the stretch
        button.clicked.connect(self.backRequested.emit)


    def buildConfirm(self) -> None:
        """
        Creates the confirm button, wired to onConfirmClicked.
        """
        self.confirmButton = QPushButton("Use This Folder")
        self.confirmButton.setObjectName("confirmButton")
        self.footerRow.addWidget(self.confirmButton)   # right of the stretch
        self.confirmButton.clicked.connect(self.onConfirmClicked)


    # handlers - respond to a click (run every time the user acts)
    def onUseDefaultClicked(self) -> None:
        """
        Fills the path field with the recommended default. Still requires confirm to actually apply it.
        """
        self.pathInput.setText(BACKUP_DESTINATION)


    def onConfirmClicked(self) -> None:
        """
        Validates the typed path via LocalFolder.setDestination, then emits destinationConfirmed, or shows an error if the folder can't be used.
        """
        path = self.pathInput.text().strip()
        if not path:
            self.showError("Please type a folder path.")
            return
        if self.local.setDestination(path):
            self.destinationConfirmed.emit()
        else:
            self.showError(
                "That folder can't be used as a backup destination. It may be a "
                "drive root, a file rather than a folder, or hold too many files "
                "to check against. Please pick a dedicated backup folder."
            )


    def showError(self, message: str) -> None:
        """
        Shows message in a QMessageBox, so errors surface somewhere other than the terminal.
        """
        error = QMessageBox(self)
        error.setWindowTitle("PixVault")
        error.setIcon(QMessageBox.Icon.Warning)
        error.setText("An Error Has Occurred:")
        error.setInformativeText(str(message))
        error.setStandardButtons(QMessageBox.StandardButton.Ok)
        error.setDefaultButton(QMessageBox.StandardButton.Ok)
        error.button(QMessageBox.StandardButton.Ok).setObjectName("confirmButton")
        error.exec()
