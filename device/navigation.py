from device.adb import ADB


class FileNavigation():
    """Handles filesystem navigation on an Android device using the ADB."""
    IMAGE_TYPES = (
        ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff",
    )

    RAW_TYPES = (
        ".dng", ".raw", ".arw", ".cr2", ".cr3", ".crw", ".nef", ".nrw", ".orf", ".raf", ".rw2", ".srw", ".pef", ".sr2", ".erf", ".kdc", ".3fr", ".mef", ".mos", ".iiq", ".x3f",
    )

    VIDEO_TYPES = (
        ".mp4", ".m4v", ".mov", ".3gp", ".3g2", ".mkv", ".webm", ".avi", ".wmv", ".flv", ".f4v", ".mpg", ".mpeg", ".mpe", ".m2v", ".ts", ".m2ts", ".mts", ".ogv", ".vob", ".asf", ".divx", ".rm", ".rmvb", ".mxf",
    )
    MEDIA_TYPES = IMAGE_TYPES + RAW_TYPES + VIDEO_TYPES

    def __init__(self) -> None:
        # Path segments, joined on demand by currentPath().
        self.currentLocation: list[str] = ["sdcard"]
        self.mediaFiles: list[str] = [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]
        self.adb: ADB = ADB()
        self.folderContence = []
        self.mediaFiles: tuple[str] = self.MEDIA_TYPES

    def goBack(self) -> None:
        """Steps up one folder, stopping at /sdcard."""
        if len(self.currentLocation) > 1:
            self.currentLocation.pop(-1)
        print(self.currentLocation)

    def currentPath(self) -> str:
        """Returns the current location as a printable path string."""
        return "/".join(self.currentLocation)

    def listFolders(self, folderContents: list[str]) -> list[str]:
        """Returns just the subfolders at the current location."""
        folders = []
        for name in folderContents:
            if not name.lower().endswith(self.mediaFiles):
                folders.append(name)
        return folders

    def listMediaFiles(self, folderContents: list[str]) -> list[str]:
        """Returns just the images/videos at the current location."""
        files = []
        for name in folderContents:
            if name.lower().endswith(self.mediaFiles):
                files.append(name)
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
                raise ValueError("Unable to find folder, please specify a real folder.")
        else:
            raise RuntimeError(f"Unable to detect a connected device, please connect or check the connection of your device \n{deviceConnected}")