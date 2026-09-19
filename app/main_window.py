from app.saving_view import SavingScreen
from app.navigation_view import NavigationScreen
from app.destination_view import DestinationScreen
from app.progress_view import ProgressScreen
from app.success_view import SuccessScreen

from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtGui import QCloseEvent

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
        self.progressScr = ProgressScreen(saver)
        self.progressScr.buildScreen()
        self.successScr = SuccessScreen(saver)
        self.successScr.buildScreen()

        # add the screens to the stack
        self.stack.addWidget(self.navigationScr)
        self.stack.addWidget(self.destinationScr)
        self.stack.addWidget(self.savingScr)
        self.stack.addWidget(self.progressScr)
        self.stack.addWidget(self.successScr)

        # when to transition between screens
        self.navigationScr.folderConfirmed.connect(self.onDeviceFolderChosen)
        self.destinationScr.backRequested.connect(self.showNavigation)
        self.destinationScr.destinationConfirmed.connect(self.showSaving)
        self.savingScr.reviewFinished.connect(self.showProgress)
        self.progressScr.savingFinished.connect(self.showSuccess)
        self.successScr.restartRequested.connect(self.startAgain)
        self.successScr.quitRequested.connect(self.close)

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


    def showProgress(self):
        """
        Bring the progress screen forward, then start pulling the files the user kept
        """
        self.stack.setCurrentWidget(self.progressScr)
        self.setWindowTitle("Progress screen")
        self.progressScr.startSaving() # after the switch, as nothing kept finishes straight onto the success screen


    def showSuccess(self):
        """
        Show what was saved, and what was not, on the Success screen
        """
        self.successScr.showResults(self.progressScr.saved, self.progressScr.failed, self.progressScr.notReached())
        self.stack.setCurrentWidget(self.successScr)
        self.setWindowTitle("Success screen")


    def startAgain(self):
        """
        Back to the top of the device to pick another folder
        """
        self.navigationScr.files.goHome()
        self.showNavigation()


    def closeEvent(self, event: QCloseEvent):
        """
        Holds the window open while a backup runs, stopping it after the file in flight so nothing half written is left behind
        """
        if self.progressScr.isRunning():
            self.progressScr.cancel(closeWhenDone=True)
            event.ignore()
            return
        super().closeEvent(event)
