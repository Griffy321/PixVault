from device import FileNavigation
from visualisation import OpenImage
from app import NavigationScreen
from PySide6 import QtWidgets
import sys


def main():
    # stop
    # back
    # FileNavigation().buildPath()

    NavigationScreen()


if __name__ == "__main__":
    FileNavigation().buildPath()

    app = QtWidgets.QApplication([])
    widget = NavigationScreen()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
