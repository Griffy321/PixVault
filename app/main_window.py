from app.saving_view import SavingScreen
from app.navigation_view import NavigationScreen
from app.destination_view import DestinationScreen

from PySide6.QtWidgets import QMainWindow, QStackedWidget

class MainWidow(QMainWindow):
    """
    Owns the window itself and the stack of screens. The only object that knows there is more than one screen, or what order they come in.
    """
    def __init__(self, files, saver):
        # setting up the main window
        super().__init__()
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.devicePath = ""

        # set up the stack of screens - it fills the window, so the window shows whichever page is current
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # add all the classes that exist under the stack take the class that interacts with the device
        self.navigationScr = NavigationScreen(files)
        self.navigationScr.buildScreen()
        self.destinationScr = DestinationScreen(saver.local)
        self.destinationScr.buildScreen()
        self.savingScr = SavingScreen(saver)
        self.savingScr.buildScreen()

        # add the screens to the stack
        self.stack.addWidget(self.navigationScr)
        self.stack.addWidget(self.destinationScr)
        self.stack.addWidget(self.savingScr)

        # when to transition between screens
        self.navigationScr.folderConfirmed.connect(self.onDeviceFolderChosen)
        self.destinationScr.backRequested.connect(self.showNavigation)
        self.destinationScr.destinationConfirmed.connect(self.showSaving)

        # the start
        self.showNavigation()


    def showNavigation(self):
        """
        Show the Navigation screen to the user
        """
        self.navigationScr.refresh()
        self.stack.setCurrentWidget(self.navigationScr)
        self.setWindowTitle("Navigation screen")


    def onDeviceFolderChosen(self, path: str):
        """
        Stores the confirmed device folder, then shows the Destination screen
        """
        self.devicePath = path
        self.stack.setCurrentWidget(self.destinationScr)
        self.setWindowTitle("Destination screen")


    def showSaving(self):
        """
        Start the backup for the stored device folder, then bring the saving screen forward
        """
        self.savingScr.startBackup(self.devicePath)
        self.stack.setCurrentWidget(self.savingScr)
        self.setWindowTitle("Saving screen")
