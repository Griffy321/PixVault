from device.adb import ADB


class FileNavigation():
    """Handles filesystem navigation on an Android device using the ADB."""

    def __init__(self) -> None:
        # Path segments, top-level first - joined on demand by currentPath().
        self.currentLocation: list[str] = ["sdcard"]
        self.mediaFiles: list[str] = [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]
        self.adb: ADB = ADB()
        self.folderContence = []


    def goBack(self) -> None:
        """Steps up one folder, stopping at /sdcard."""
        if len(self.currentLocation) > 1:
            self.currentLocation.pop(-1)
        print(self.currentLocation)


    def currentPath(self) -> str:
        """Returns the current location as a printable path string."""
        return "/".join(self.currentLocation)


    # TODO: implement — see item 4 above
    def listFolders(self, folderContents: list[str]) -> list[str]:
        """Returns just the subfolders at the current location."""
        folders = []
        for string in folderContents:
            if "." in string:
                continue
            else:
                folders.append(string) # add verificatrion
        return folders

    # TODO: implement — see item 4 above
    def listMediaFiles(self, folderContents: list[str]) -> list[str]:
        """Returns just the images/videos at the current location."""
        files = []
        for string in folderContents:
            if "." in string:
                files.append(string) # add verificatrion
            else:
                continue
        return files

    def validateMove(self, userInput: str, choices: list[str]) -> bool:
        if userInput in choices:
            return True
        else:
            return False

    def buildPath(self, step: str) -> list[str] | None:
        """
        Constructs an absolute path string by appending a folder name to the base directory.
        Returns the contence of the current folder  
        """
        deviceConnected = self.adb.isDeviceConnected()
        if deviceConnected[0]:
            position = self.adb.fromHeadDir(path=self.currentPath())
            if step.lower() == "stop":
                return position
            elif step.lower() == "back":
                self.goBack()
            elif self.validateMove(userInput=step, choices=position):
                self.currentLocation.append(step) # add check on curent path here
                self.folderContence = self.adb.fromHeadDir(path=self.currentPath())
                return self.folderContence
        else:
            raise RuntimeError(f"Unable to detect a connected device, please connect or check the connection of your device \n{deviceConnected}")