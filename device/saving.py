import os
import stat
from pathlib import Path
from config import isMedia
from device.adb import ADB


class FileSaving:

    """Class to handle photo and video saving from one device to the other"""

    MAX_SCAN_FILES = 50_000
    MAX_SCAN_DEPTH = 8
    SKIP_FOLDERS = {
        "$recycle.bin", "system volume information", "windows", "programdata",
        "program files", "program files (x86)", "appdata", "node_modules", ".git",
    }

    def __init__(self):
        ###### Device file objects ######
        self.adb = ADB()
        self.devicePath = ""
        self.deviceFileContent: dict[str, int] = {}

        ###### PC file objects ######
        self.pcFiles = ""
        self.pcFolderContent: dict[str, set[int]] = {} # fileName : {bytes}, a set as one name can sit in two subfolders at different sizes
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
    # PC functions
    ################################################################################################
    def setDestination(self, folder: str) -> bool:
        """Points self.pcFiles at the folder the user picked, creating it if it isn't there yet.
        Turns down drive roots and anything too big to index"""
        target = Path(folder)
        if target.parent == target: 
            print(f"{folder} is a drive root, please pick a folder to back up into.")
            return False
        if not target.exists():
            try:
                target.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Failed to create folder {folder}: {e}")
                return False
            self.pcFiles = str(target)
            return True
        if not target.is_dir():
            print(f"{folder} is a file, please pick a folder.")
            return False
        withinBudget, seen = self.withinScanBudget(target)
        if not withinBudget:
            print(f"{folder} holds over {self.MAX_SCAN_FILES:,} files, which is too many to check against. Please pick a dedicated backup folder.")
            return False
        print(f"Destination set to {target} ({seen:,} files already there)")
        self.pcFiles = str(target)
        return True

    def isLinkedFolder(self, entry: os.DirEntry) -> bool:
        """True for a symlinked or junctioned folder, which we never follow in case it
        points back up its own path."""
        if entry.is_symlink():
            return True
        try: # is_junction() is >= Python 3.12
            attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        except OSError:
            return True
        return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)

    def walkFiles(self, root: Path):
        """Yields an entry for every file under root, ignoring system folders, links
        and anything past MAX_SCAN_DEPTH."""
        stack = [(str(root), 0)]
        while stack:
            folder, depth = stack.pop()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        try:
                            isFolder = entry.is_dir(follow_symlinks=False)
                        except OSError:
                            continue
                        if not isFolder:
                            yield entry
                        elif (depth < self.MAX_SCAN_DEPTH and entry.name.lower() not in self.SKIP_FOLDERS and not self.isLinkedFolder(entry)):
                            stack.append((entry.path, depth + 1))
            except PermissionError:
                continue # locked folder
            except OSError as e:
                print(f"Skipping {folder}: {e}") # unreadable

    def withinScanBudget(self, root: Path) -> tuple[bool, int]:
        """Counts the files under root, giving up as soon as it passes MAX_SCAN_FILES."""
        seen = 0
        for _ in self.walkFiles(root):
            seen += 1
            if seen > self.MAX_SCAN_FILES:
                return False, seen
        return True, seen

    def loadPCFolderContent(self) -> dict[str, set[int]]:
        """Fills self.pcFolderContent with the media under self.pcFiles."""
        if not self.pcFiles:
            raise RuntimeError("No destination set, call setDestination() first.")
        self.pcFolderContent = {}
        for entry in self.walkFiles(Path(self.pcFiles)):
            if not isMedia(entry.name):
                continue
            try:
                size = entry.stat().st_size
            except OSError:
                continue
            self.pcFolderContent.setdefault(entry.name.lower(), set()).add(size)
        return self.pcFolderContent


    ################################################################################################
    # De-duping functions
    ################################################################################################
    def buildBackupList(self) -> list[str]:
        """Fills self.toBackup with the files worth pulling from remoteFolder"""
        if len(self.deviceFileContent) == 0:
            raise ValueError("You currently have 0 device files selected to backup, please select a valid folder to backup")
        if len(self.pcFolderContent) == 0:
            raise ValueError("You currently have 0 PC files to compare against, please select a valid folder for comparison to be effective")
        for file in self.deviceFileContent.items():
            if file[0].lower() in self.pcFolderContent.keys():
                print("match found")
                matchingFiles = self.pcFolderContent.get(file[0].lower())
                if self.sameFile(file, matchingFiles):
                    continue
                else:
                    self.toBackup.append(file[0]) # if the name already exists but the matching file has a diffrent number of bytes then add it to the backup list, we might want to flag these files
            else:
                print("no match")
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

    def formatProgress(self, transferred: int, total: int) -> str:
        """Turns raw byte counts into a line to put on screen, e.g. "12.8 MB of 240 MB".
        Takes its numbers as arguments so it stays testable without a device attached."""
        pass

