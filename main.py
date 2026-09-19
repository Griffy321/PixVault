from device import FileNavigation
from app import MainWidow
import sys
from PySide6.QtWidgets import QApplication
from device import FileSaving
from local import LocalFolder
from history import BackupHistory
from pvlogging import setupLogging


def main():
    setupLogging()
    backup = BackupHistory()
    backup.checkForHistFile()
    backup.setupTable()
    app = QApplication(sys.argv)
    saver = FileSaving(history=backup)
    app.aboutToQuit.connect(saver.adb.killServer)
    window = MainWidow(FileNavigation(), saver)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
