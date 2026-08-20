from device import FileNavigation
from app import MainWidow
import sys
from PySide6.QtWidgets import QApplication
from device import FileSaving
from local import LocalFolder


def main():
    app = QApplication(sys.argv)
    window = MainWidow(FileNavigation(), FileSaving())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

## Call functions in this oreder when setting up saving
# deviceFiles = FileSaving(LocalFolder())
# deviceFiles.loadDeviceFolderContent("")
# deviceFiles.local.setDestination("") # if this returns true then continue, otherwise pick another folder
# deviceFiles.local.loadPCFolderContent() # callricht away when above returns true
# print(deviceFiles.saveFile("")) # for each file in the backup list