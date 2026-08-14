import os
import stat
from pathlib import Path

from device.adb import ADB
from device.navigation import FileNavigation


class FileSaving:

    """Class to handle photo and video saving from one device to the other"""

    MAX_SCAN_FILES = 50_000
    MAX_SCAN_DEPTH = 8
    SKIP_FOLDERS = {
        "$recycle.bin", "system volume information", "windows", "programdata",
        "program files", "program files (x86)", "appdata", "node_modules", ".git",
    }

    def __init__(self):
        self.deviceFiles = ADB()
        self.pcFiles = ""
        self.pcFolderContent: dict[str, list[tuple[Path, int]]] = {}
        self.toBackup = []
        self.failedBackup = []
        self.fileSizes = {}
        self.totalBytes = 0
        self.transferredBytes = 0

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

    def loadFolderContent(self) -> dict[str, list[tuple[Path, int]]]:
        """Fills self.pcFolderContent with the media under self.pcFiles."""
        if not self.pcFiles:
            raise RuntimeError("No destination set, call setDestination() first.")

        self.pcFolderContent = {}
        for entry in self.walkFiles(Path(self.pcFiles)):
            if not entry.name.lower().endswith(FileNavigation.MEDIA_TYPES):
                continue
            try:
                size = entry.stat().st_size
            except OSError:
                continue
            self.pcFolderContent.setdefault(entry.name.lower(), []).append((Path(entry.path), size))
        return self.pcFolderContent

    def localPathFor(self, fileName: str) -> Path:
        """Returns where a device file will land inside self.pcFiles, keeping its
        original name so IMG_420_69_67.jpg stays IMG_420_69_67.jpg."""
        pass

    # working out what actually needs copying
    def alreadySaved(self, fileName: str) -> bool:
        """True when this photo is already in self.pcFolderContent and can be skipped.
        Re-running a backup is the normal case, so this is what keeps it quick."""
        pass

    def sameFile(self, remotePath: str, localPath: Path) -> bool:
        """Compares the device copy with the local one, most cheaply on byte size.
        Separates a genuine duplicate from two different photos sharing a name."""
        pass

    def resolveNameClash(self, localPath: Path) -> Path:
        """Returns a free path when a different photo already holds that name,
        e.g. IMG_0421 (1).jpg, so two devices cannot overwrite each other."""
        pass

    def buildBackupList(self, remoteFolder: str, fileNames: list[str]) -> list[str]:
        """Fills self.toBackup with the files worth pulling from remoteFolder.
        Gives the UI a total to count against before any copying starts."""
        pass

    # doing the copy
    def saveFile(self, remotePath: str) -> Path | None:
        """Pulls one photo to its local path via self.deviceFiles.adb.pull().
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

    # telling the user how far along the backup is
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

if __name__ == "__main__": # run from the project root with: python -m device.saving
    saver = FileSaving()
    if saver.setDestination("C:/Android S23 Pics Backup"):
        index = saver.loadFolderContent()
        print(f"Indexed {len(index)} names, {sum(len(v) for v in index.values())} files")
        for name, copies in list(index.items())[:5]:
            print(f"  {name}: {copies}")