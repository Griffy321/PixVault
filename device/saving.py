from pathlib import Path
from device.adb import ADB
from history import BackupHistory
from local import LocalFolder
import sqlite3
from pvlogging import getLogger

log = getLogger(__name__)


class FileSaving:

    """
    Class to handle photo and video saving from one device to the other, this class mainly looks at the device.
    """

    def __init__(self, local: LocalFolder = None, history: BackupHistory = None):
        ###### Device file objects ######
        self.adb = ADB()
        self.devicePath = ""
        self.deviceFileContent: dict[str, int] = {}

        ###### PC file objects ######
        self.local = local if local is not None else LocalFolder()
        self.history = history if history is not None else BackupHistory()
        self.toBackup = []
        self.failedBackup = []
        self.totalBytes = 0
        self.transferredBytes = 0


    @property
    def devicePath(self):
        return self._devicePath


    @devicePath.setter
    def devicePath(self, value):
        if str(value) == "":
            self._devicePath = value
        elif str(value).endswith("/"):
            self._devicePath = value
        else:
            self._devicePath = value + "/"


    ################################################################################################
    # Device functions
    ################################################################################################
    def loadDeviceFolderContent(self, deviceFilePath: str) -> None:
        try:
            self.deviceFileContent = self.adb.backupDict(deviceFilePath)
            self.devicePath = deviceFilePath
        except FileNotFoundError as e:
            print(f"Error: {e}")


    ################################################################################################
    # De-duping functions
    ################################################################################################
    def buildBackupList(self) -> list[str]:
        """
        Fills self.toBackup with the files worth pulling from remoteFolder
        """
        if len(self.deviceFileContent) == 0:
            raise ValueError("You currently have 0 device files selected to backup, please select a valid folder to backup")
        historicBackups = self.pullBackupHistory()

        knownFiles = self.local.pcFolderContent.keys() | historicBackups.keys()
        
        for file in self.deviceFileContent.items():
            if file[0].lower() in knownFiles:
                matchingFilesLocal = self.local.pcFolderContent.get(file[0].lower())
                matchingFilesHist = historicBackups.get(file[0].lower())
                matchingFiles = (matchingFilesLocal or set()).union(matchingFilesHist or set())
                if self.sameFile(file, matchingFiles):
                    continue
                else:
                    self.toBackup.append(file[0]) # if the name already exists but the matching file has a diffrent number of bytes then add it to the backup list, we might want to flag these files
            else:
                self.toBackup.append(file[0])
        return self.toBackup


    def sameFile(self, deviceFile: dict, pcFiles: set[int]) -> bool:
        """
        Compares the device copy with the local one on byte size, returns true if the file already exists.

        Params:
        - deviceFile is a dict of fileName : bytes
        - pcFiles is a set of ints that have the same name as the deviceFile - this function compares their bytes
        """
        deviceFileBytes = deviceFile[1]
        for fileBytes in pcFiles:
            if int(deviceFileBytes) == int(fileBytes):
                return True
        return False


    def pullBackupHistory(self):
        """
        Pulls all files that have ever been backed up amd returns a list of lists [[file_name, bytes], [file_name, bytes]] to be compared against.
        """
        content = {}
        connection = sqlite3.connect(self.history.tableLocation)
        sqlEngine = connection.cursor()
        try:
            backupData = sqlEngine.execute("""
                select 
                    file_name,
                    file_bytes
                from 
                    saved_files
                where 
                    deleted_at is null
                    and file_bytes is not null
            """)
            for fileName, fileBytes in backupData:
                content.setdefault(fileName.lower(), set()).add(int(fileBytes))
        except sqlite3.Error as e:
            log.warning("Failed to select saved files from the db table error: %s", e)
        finally:
            connection.close()
        return content


    ################################################################################################
    # Saving functions
    ################################################################################################
    def verifySaved(self, fileName: str) -> bool:
        """
        Confirms the local copy is complete after a pull, so a half-written file from a yanked cable is not counted as backed up.
        """
        deviceFileSize = int(self.deviceFileContent.get(fileName))
        if deviceFileSize is None:
            raise ValueError("Unable to find the fileName in deviceFileContent.")
        localFile = Path(self.local.pcFiles + fileName)
        if localFile.exists() and int(localFile.stat().st_size) == deviceFileSize:
            return True
        return False


    def saveFile(self, remotePath: str):
        """
        Pulls one photo to its local path. Returns the path written, or None if it was skipped or failed.
        """
        if len(self.local.pcFiles) == 0:
            raise FileNotFoundError("Please specify the folder where you want files to be saved to using local.setDestination()")
        if len(self.devicePath) == 0:
            raise FileNotFoundError("Please specify the device where you want to pull files from using loadDeviceFolderContent()")
        deviceFile = self.devicePath + remotePath
        result = self.adb.pullFiles(remotePath=deviceFile, localPath=self.local.pcFiles)
        if result is True and self.verifySaved(remotePath) is True:
            self.history.recordFile(remotePath.lower(), self.deviceFileContent.get(remotePath))
            return str(self.local.pcFiles + remotePath).replace("\\", "/")
        return "failed"


    def saveAll(self):
        """Runs saveFile over self.toBackup and returns each file's outcome
        ("saved" / "skipped" / "failed") for the progress view to report.
        Calls onProgress(transferredBytes, totalBytes) after each file, if given."""
        for file in self.toBackup:
            result = self.saveFile(file)
            if result == "failed":
                self.failedBackup.append(file)
            self.transferredBytes += self.deviceFileContent.get(file)
            yield file


    ################################################################################################
    # UI functions
    ################################################################################################
    def totalToTransfer(self) -> int:
        """
        Sets self.totalBytes to the summed size of everything in self.toBackup.
        Run after buildBackupList, as it is the fixed "of 240 MB" half of the display.
        """
        self.totalBytes = sum(self.deviceFileContent.get(file, 0) for file in self.toBackup)
        return self.totalBytes


    def bytesRemaining(self) -> int:
        """
        Returns how many bytes of the backup are still to come.
        """
        return self.totalBytes - self.transferredBytes