from PySide6.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout , QHBoxLayout, QLineEdit, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Signal
from device import FileNavigation

STYLESHEET = """
QWidget {
    background-color: #f4f5f7;
    color: #1f2430;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QLabel#pathLabel {
    color: #5a6270;
    font-size: 12px;
    padding-bottom: 2px;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 7px 10px;
}
QLineEdit:focus {
    border-color: #3d7eff;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 7px 8px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: #eef1f6;
}
QListWidget::item:selected {
    background-color: #3d7eff;
    color: #ffffff;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 7px 16px;
}
QPushButton:hover {
    background-color: #eaecf1;
}
QPushButton:pressed {
    background-color: #dee1e8;
}

QPushButton#confirmButton {
    background-color: #3d7eff;
    border-color: #3d7eff;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#confirmButton:hover {
    background-color: #2f6cea;
}
QPushButton#confirmButton:disabled {
    background-color: #dfe2e8;
    border-color: #dfe2e8;
    color: #9aa1ad;
}

QMessageBox {
    background-color: #ffffff;
}

/* Internal object names Qt gives the two lines of a message box. */
QMessageBox QLabel#qt_msgbox_label {
    color: #1f2430;
    font-size: 15px;
    font-weight: 600;
    min-width: 320px;           /* stops one-word errors making a tiny box */
    padding-bottom: 4px;
}
QMessageBox QLabel#qt_msgbox_informativelabel {
    color: #5a6270;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 78px;
    padding: 7px 18px;
}
"""


class NavigationScreen(QWidget):
    """
    The screen for picking which folder to back up. Shows the current path,
    lists what is in it, and lets you move up and down until you confirm one.

    Only deals with widgets - the actual path work belongs to
    FileNavigation held in self.files, which buildScreen() is given.
    """

    folderConfirmed = Signal(str)

    def __init__(self):
        super().__init__() # a way to refer to the super class without calling
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("PixVault - Choose a folder")
        self.setStyleSheet(STYLESHEET)

    # builders - make a widget and add it to the layout (run once)

    def buildScreen(self, files:FileNavigation) -> None:
        """Stores files as self.files, runs the builders in display order, then
        refreshes to draw the starting folder."""
        self.files = files
        self.buildPathLabel()
        self.buildSearchFolder()
        self.buildFileList()
        self.buildFooter()
        self.buildBack()
        self.buildConfirm()
        self.refresh()

    def buildPathLabel(self) -> None:
        """Creates self.pathLabel, the "you are here" line. refresh() updates it."""
        self.pathLabel = QLabel(f"You're currently in : {self.files.currentPath()}")
        self.pathLabel.setObjectName("pathLabel")
        self.layout.addWidget(self.pathLabel)

    def buildSearchFolder(self):
        """Creates the search bar and its button on one row, wired to onSearchClicked."""
        row = QHBoxLayout()
        row.setSpacing(8)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Type a folder name, then press Enter")
        button = QPushButton("Search Folder")

        row.addWidget(self.searchBar)
        row.addWidget(button)
        self.layout.addLayout(row)

        button.clicked.connect(lambda: self.onSearchClicked(self.searchBar.text()))
        self.searchBar.returnPressed.connect(lambda: self.onSearchClicked(self.searchBar.text()))

    def buildFileList(self):
        """Creates self.contentsList and wires double-clicks to onItemDoubleClicked."""
        self.contentsList = QListWidget()
        self.layout.addWidget(self.contentsList, stretch=1)
        self.contentsList.itemDoubleClicked.connect(lambda item: self.onItemDoubleClicked(item))

    def buildFooter(self) -> None:
        """Creates self.footerRow, the row the two buttons sit in."""
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.footerRow.addStretch()
        self.layout.addLayout(self.footerRow)

    def buildBack(self):
        """Creates the back button, wired to onBackClicked."""
        button = QPushButton("Go Back")
        self.footerRow.insertWidget(0, button)      # left of the stretch
        button.clicked.connect(lambda: self.onBackClicked())

    def buildConfirm(self) -> None:
        """Creates the "Back Up This Folder" button. Connects to onConfirmClicked;
        worth disabling while the folder holds no media."""
        self.confirmButton = QPushButton("Select Folder for Backup")
        self.confirmButton.setObjectName("confirmButton")
        self.footerRow.addWidget(self.confirmButton)   # right of the stretch
        self.confirmButton.clicked.connect(lambda: self.onConfirmClicked())

    # handlers - respond to a click (run every time the user acts)

    def onBackClicked(self) -> None:
        """Steps up one folder and redraws."""
        self.files.goBack()
        self.refresh()

    def onSearchClicked(self, step):
        """Jumps to the folder typed in the search bar and redraws."""
        try:
            self.files.buildPath(step)
            self.refresh()
        except Exception:
            self.showError("Please specify a folder from the ones shown on the page.")

    def onItemDoubleClicked(self, item: QListWidgetItem) -> None:
        """Enters the double-clicked row if it is a folder. Media rows are ignored."""
        try:
            folder = item.text().replace("/", "")
            if folder in self.files.listFolders(self.listing):
                self.files.buildPath(folder)
                self.refresh()
            else:
                self.showError("Please double click a folder to use this action.")
        except Exception as e:
            self.showError(e)

    def onConfirmClicked(self) -> None:
        """Emits folderConfirmed with the current path. Everything in that folder
        gets backed up, so there is no per-file selection to gather."""
        self.folderConfirmed.emit(self.files.currentPath())

    # shared - the work both of the above lean on

    def refresh(self) -> None:
        """Re-reads the current folder from the device and redraws the label and
        list. Every action that changes location ends by calling this."""
        path = self.files.currentPath()
        listing = self.files.adb.fromHeadDir(path=path)
        if path == "sdcard" and len(listing) == 0: # check the device is still connected when in a place that should have files
            self.showError("Please check your device is connected")
        else:
            self.populateList(listing) # contentsList.clear() then addItem() each row
            self.pathLabel.setText(f"You're currently in : {path}")
            self.updateConfirmButton()

    def populateList(self, folderContents: list[str]) -> None:
        """Refills the list from a raw ADB listing, folders first with a trailing
        "/" so onItemDoubleClicked can tell them from media."""
        self.listing = folderContents
        self.contentsList.clear()

        folders = self.files.listFolders(folderContents)
        for folder in folders:
            self.contentsList.addItem(f"{folder}/")

        files = self.files.listMediaFiles(folderContents)
        for file in files:
            self.contentsList.addItem(file)

    def mediaInCurrentFolder(self) -> list[str]:
        """Returns the media files in the current folder, for the confirm button's
        count and enabled state. Reads the listing refresh() already fetched rather
        than asking the device again."""
        return self.files.listMediaFiles(self.listing)

    def updateConfirmButton(self) -> None:
        """Enables the confirm button only when the folder holds media, and shows the
        count so the user knows what they are committing to before they click."""
        count = len(self.mediaInCurrentFolder())
        self.confirmButton.setEnabled(count > 0)
        if count:
            self.confirmButton.setText(f"Back Up {count} Item{'' if count == 1 else 's'}")
        else:
            self.confirmButton.setText("No Media In This Folder")

    def showError(self, message: str) -> None:
        """Shows message in a QMessageBox, so errors surface somewhere other than
        the terminal."""
        error = QMessageBox(self)
        error.setWindowTitle("PixVault")
        error.setIcon(QMessageBox.Icon.Warning)
        error.setText("An Error Has Occurred:")
        error.setInformativeText(str(message))
        error.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close)
        error.setDefaultButton(QMessageBox.StandardButton.Ok)
        error.button(QMessageBox.StandardButton.Ok).setObjectName("confirmButton")
        error.exec()