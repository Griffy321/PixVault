import os
import stat
from pathlib import Path
from config import isMedia


class LocalFolder:

    """Class to handle scanning the folder on this PC that we back up into"""

    MAX_SCAN_FILES = 50_000
    MAX_SCAN_DEPTH = 8
    SKIP_FOLDERS = {
        "$recycle.bin", "system volume information", "windows", "programdata",
        "program files", "program files (x86)", "appdata", "node_modules", ".git",
    }


    def __init__(self):
        self.pcFiles = ""
        self.pcFolderContent: dict[str, set[int]] = {} # fileName : (bytes, bytes), a set as one name can sit in two subfolders at different sizes


    @property
    def pcFiles(self):
        return self._pcFiles


    @pcFiles.setter
    def pcFiles(self, value):
        if str(value) == "":
            self._pcFiles = value # do not use the setter logic if self.pcFiles has not been set yet 
        elif str(value).endswith("/"):
            self._pcFiles = value
        else:
            self._pcFiles = str(value) + "/"


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
            self.pcFiles = str(target) # calls the setter automatically to check and set the value
            return True
        if not target.is_dir():
            print(f"{folder} is a file, please pick a folder.")
            return False
        withinBudget, seen = self.withinScanBudget(target)
        if not withinBudget:
            print(f"{folder} holds over {self.MAX_SCAN_FILES:,} files, which is too many to check against. Please pick a dedicated backup folder.")
            return False
        self.pcFiles = str(target) # calls the setter automatically to check and set the value
        print(f"Destination set to {target} ({seen:,} files already there)")
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