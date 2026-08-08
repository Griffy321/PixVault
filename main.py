from device import FileNavigation
from visualisation import OpenImage
from app import NavigationScreen
import sys
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    files = FileNavigation()
    nav = NavigationScreen()
    nav.buildScreen(files)
    nav.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

