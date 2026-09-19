from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, QThread
from device import FileSaving
from config import STYLESHEET
from app.progress_chart import ProgressChart
from app.saving_view import SavingScreen
from pvlogging import getLogger

log = getLogger(__name__)


class BackupWorker(QThread):
    """
    Runs FileSaving.saveAll on its own thread so the window keeps drawing while adb pulls.
    Only checks cancelled between files, so a cancel always lets the file in flight finish.
    """

    fileStarted = Signal(str)
    fileFinished = Signal(str, bool, object) # object not int, a Qt int is 32 bit and a backup can pass 2 GB


    def __init__(self, saving: FileSaving):
        super().__init__()
        self.saving = saving
        self.cancelled = False


    def run(self) -> None:
        for fileName, saved in self.saving.saveAll(onStart=self.fileStarted.emit):
            self.fileFinished.emit(fileName, saved, self.saving.transferredBytes)
            if self.cancelled:
                log.info("Backup cancelled after %s", fileName)
                break


class ProgressScreen(QWidget):
    """
    The screen shown while the kept files are pulled onto this PC.

    The chart climbs towards the backup's total as each file lands. self.saved and self.failed
    fill in as it goes, for the success screen to report once savingFinished fires.
    """

    savingFinished = Signal()


    def __init__(self, saving: FileSaving):
        super().__init__()
        self.saving = saving
        self.worker: BackupWorker | None = None
        self.saved: list[str] = []
        self.failed: list[str] = []
        self.currentFile = ""
        self.closeWhenDone = False
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
        self.buildChart()
        self.buildFooter()
        self.buildCancelButton()


    def buildHeader(self) -> None:
        """
        Creates the title, the file being pulled now, and the running total.
        """
        self.title = QLabel("Saving your photos")
        self.title.setObjectName("title")
        self.currentLabel = QLabel()
        self.currentLabel.setObjectName("pathLabel")
        self.figureLabel = QLabel()
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.currentLabel)
        self.layout.addWidget(self.figureLabel)
        self.layout.addSpacing(4)


    def buildChart(self) -> None:
        """
        Creates self.chart, the line climbing towards the total.
        """
        self.chart = ProgressChart()
        self.layout.addWidget(self.chart, stretch=1)


    def buildFooter(self) -> None:
        """
        Creates self.footerRow, the row the cancel button sits in.
        """
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.footerRow.addStretch()
        self.layout.addSpacing(4)
        self.layout.addLayout(self.footerRow)


    def buildCancelButton(self) -> None:
        """
        Creates the cancel button, wired to onCancelClicked.
        """
        self.cancelButton = QPushButton("Cancel")
        self.footerRow.addWidget(self.cancelButton)
        self.cancelButton.clicked.connect(self.onCancelClicked)


    # handlers - respond to the user or the worker
    def onCancelClicked(self) -> None:
        """
        Stops the backup once the file in flight has finished, so nothing half written reaches the destination.
        """
        self.cancel()


    def onFileStarted(self, fileName: str) -> None:
        """
        Names the file being pulled now.
        """
        self.currentFile = fileName
        if not self.worker.cancelled:
            self.currentLabel.setText(f"Saving {fileName}")


    def onFileFinished(self, fileName: str, saved: bool, soFar: int) -> None:
        """
        Adds the file to the chart and moves the running total on.
        """
        if saved:
            self.saved.append(fileName)
        else:
            self.failed.append(fileName)
        self.chart.addFile(fileName, self.saving.deviceFileContent.get(fileName, 0), saved, soFar)
        self.updateFigure(soFar)


    def onWorkerFinished(self) -> None:
        """
        Runs once the last file is in, or a cancel has taken effect.
        """
        self.worker.wait() # finished fires just before the thread ends
        self.worker = None
        if self.closeWhenDone:
            self.window().close()
            return
        self.savingFinished.emit()


    # shared - the work the above lean on
    def startSaving(self) -> None:
        """
        Totals up the kept files, resets the chart and starts the worker. With nothing kept there is nothing to pull, so it finishes straight away.
        """
        self.saved = []
        self.failed = []
        self.currentFile = ""
        self.closeWhenDone = False
        files = len(self.saving.toBackup)
        self.chart.reset(self.saving.totalToTransfer(), files)
        self.cancelButton.setEnabled(True)
        self.cancelButton.setText("Cancel")
        self.updateFigure(0)
        if files == 0:
            self.savingFinished.emit()
            return
        self.currentLabel.setText("Getting ready...")
        self.worker = BackupWorker(self.saving)
        self.worker.fileStarted.connect(self.onFileStarted)
        self.worker.fileFinished.connect(self.onFileFinished)
        self.worker.finished.connect(self.onWorkerFinished)
        log.info("Saving %s files, %s bytes", files, self.saving.totalBytes)
        self.worker.start()


    def cancel(self, closeWhenDone: bool = False) -> None:
        """
        Asks the worker to stop after the current file. closeWhenDone shuts the window once it has.
        """
        if not self.isRunning():
            return
        self.closeWhenDone = self.closeWhenDone or closeWhenDone
        self.worker.cancelled = True
        self.cancelButton.setEnabled(False)
        self.cancelButton.setText("Stopping...")
        if self.currentFile:
            self.currentLabel.setText(f"Stopping once {self.currentFile} has finished saving")
        else:
            self.currentLabel.setText("Stopping...") # cancelled before the first file started


    def isRunning(self) -> bool:
        return self.worker is not None and self.worker.isRunning()


    def notReached(self) -> list[str]:
        """
        The kept files a cancel stopped us getting to.
        """
        return self.saving.toBackup[len(self.saved) + len(self.failed):]


    def updateFigure(self, soFar: int) -> None:
        """
        Refreshes the "12.8 MB of 240 MB" line under the title.
        """
        done = len(self.saved) + len(self.failed)
        self.figureLabel.setText(f"{SavingScreen.formatProgress(soFar, self.saving.totalBytes)}   ·   {done} of {len(self.saving.toBackup)} files")
