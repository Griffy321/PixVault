from device import FileNavigation
from app import MainWidow
import sys
from PySide6.QtWidgets import QApplication
from device import FileSaving
from local import LocalFolder
from pvlogging import setupLogging


def main():
    setupLogging()
    app = QApplication(sys.argv)
    window = MainWidow(FileNavigation(), FileSaving())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    