from device import FileNavigation
from visualisation import OpenImage
from app import NavigationScreen
import sys
from PySide6.QtWidgets import QApplication
from device import FileSaving


def main():
    # app = QApplication(sys.argv)
    # files = FileNavigation()
    # nav = NavigationScreen()
    # nav.buildScreen(files)
    # nav.show()
    # sys.exit(app.exec())
    ### ### ### ### ### ###

    backupFiles = FileSaving()
    print(backupFiles.loadDeviceFolderContent("sdcard/DCIM/Cool Stuff"))
    backupFiles.local.setDestination("C:/Android S23 Pics Backup")
    filesInDestination = backupFiles.local.loadPCFolderContent()
    print(backupFiles.buildBackupList())
    # count = 0
    # while count < 3:
    #     print(list(backupFiles.deviceFiles.items())[count])
    #     print(list(filesInDestination.items())[count])
    #     count += 1
    # print(len(filesInDestination))


if __name__ == "__main__":
    main()

