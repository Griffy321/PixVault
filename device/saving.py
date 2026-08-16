from pathlib import Path
from device.adb import ADB
from local import LocalFolder


class FileSaving:

    """Class to handle photo and video saving from one device to the other"""

    def __init__(self):
        ###### Device file objects ######
        self.adb = ADB()
        self.devicePath = ""
        self.deviceFileContent: dict[str, int] = {}

        ###### PC file objects ######
        self.local = LocalFolder()
        self.toBackup = []
        self.failedBackup = []
        self.fileSizes = {}
        self.totalBytes = 0
        self.transferredBytes = 0

    ################################################################################################
    # Device functions
    ################################################################################################
    def loadDeviceFolderContent(self, remoteFilePath: str) -> None:
        try:
            self.deviceFileContent = self.adb.backupDict(remoteFilePath)
            self.devicePath = remoteFilePath
        except FileNotFoundError as e:
            print(f"Error: {e}")

    ################################################################################################
    # De-duping functions
    ################################################################################################
    def buildBackupList(self) -> list[str]:
        """Fills self.toBackup with the files worth pulling from remoteFolder"""
        if len(self.deviceFileContent) == 0:
            raise ValueError("You currently have 0 device files selected to backup, please select a valid folder to backup")
        if len(self.local.pcFolderContent) == 0:
            raise ValueError("You currently have 0 PC files to compare against, please select a valid folder for comparison to be effective")
        for file in self.deviceFileContent.items():
            if file[0].lower() in self.local.pcFolderContent.keys():
                matchingFiles = self.local.pcFolderContent.get(file[0].lower())
                if self.sameFile(file, matchingFiles):
                    continue
                else:
                    self.toBackup.append(file[0]) # if the name already exists but the matching file has a diffrent number of bytes then add it to the backup list, we might want to flag these files
            else:
                self.toBackup.append(file[0])
        return self.toBackup

    def sameFile(self, deviceFile: dict, pcFiles: set[int]) -> bool:
        """Compares the device copy with the local one on byte size, returns true if the file already exists."""
        deviceFileBytes = deviceFile[1]
        for fileBytes in pcFiles:
            if int(deviceFileBytes) == int(fileBytes):
                return True
        return False


    ################################################################################################
    # Saving functions
    ################################################################################################
    def saveFile(self, remotePath: str) -> Path | None:
        """Pulls one photo to its local path via self.deviceFileContent.adb.pull().
        Returns the path written, or None if it was skipped or failed."""
        pass

    def saveAll(self, onProgress=None) -> dict[str, str]:
        """Runs saveFile over self.toBackup and returns each file's outcome
        ("saved" / "skipped" / "failed") for the progress view to report.
        Calls onProgress(transferredBytes, totalBytes) after each file, if given."""
        pass

    def verifySaved(self, remotePath: str, localPath: Path) -> bool:
        """Confirms the local copy is complete after a pull, so a half-written file
        from a yanked cable is not counted as backed up."""
        pass

    ################################################################################################
    # UI functions
    ################################################################################################
    def loadFileSizes(self, remoteFolder: str) -> dict[str, int]:
        """Fills self.fileSizes from one sizesInFolder() call on remoteFolder.
        Also what sameFile() compares against, so it is read once and shared."""
        pass

    def totalToTransfer(self) -> int:
        """Sets self.totalBytes to the summed size of everything in self.toBackup.
        Run after buildBackupList, as it is the fixed "of 240 MB" half of the display."""
        pass

    def bytesRemaining(self) -> int:
        """Returns how many bytes of the backup are still to come."""
        pass


