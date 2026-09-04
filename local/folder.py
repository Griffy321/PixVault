import os
import stat
from pathlib import Path
from config import isMedia
from pvlogging import getLogger

log = getLogger(__name__)


class LocalFolder:

    """
    Class to handle scanning the folder on this PC that we back up into
    """

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
        """
        Points self.pcFiles at the folder the user picked, creating it if it isn't there yet.
        Turns down drive roots and anything too big to index
        """
        target = Path(folder)
        log.debug("Checking %s as a backup destination", folder)
        if target.parent == target:
            log.warning("%s is a drive root, please pick a folder to back up into.", folder)
            return False
        if not target.exists():
            log.info("%s does not exist yet, creating it", folder)
            try:
                target.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                log.error("Failed to create folder %s: %s", folder, e)
                return False
            self.pcFiles = str(target) # calls the setter automatically to check and set the value
            log.info("Destination set to %s (new empty folder)", target)
            return True
        if not target.is_dir():
            log.warning("%s is a file, please pick a folder.", folder)
            return False
        withinBudget, seen = self.withinScanBudget(target)
        if not withinBudget:
            log.warning("%s holds over %s files, which is too many to check against. Please pick a dedicated backup folder.", folder, f"{self.MAX_SCAN_FILES:,}")
            return False
        self.pcFiles = str(target) # calls the setter automatically to check and set the value
        log.info("Destination set to %s (%s files already there)", target, f"{seen:,}")
        return True


    def isLinkedFolder(self, entry: os.DirEntry) -> bool:
        """
        True for a symlinked or junctioned folder, which we never follow in case it points back up its own path.
        """
        if entry.is_symlink():
            log.debug("%s is a symlink, not following it", entry.path)
            return True
        try: # is_junction() is >= Python 3.12
            attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        except OSError as e:
            log.debug("Could not stat %s, treating it as a link so we do not follow it: %s", entry.path, e)
            return True
        isLink = bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
        if isLink:
            log.debug("%s is a junction, not following it", entry.path)
        return isLink


    def walkFiles(self, root: Path):
        """
        Yields an entry for every file under root, ignoring system folders, links and anything past MAX_SCAN_DEPTH.
        """
        log.debug("Walking %s", root)
        stack = [(str(root), 0)]
        foldersRead = 0
        filesFound = 0
        foldersSkipped = 0
        while stack:
            folder, depth = stack.pop()
            try:
                with os.scandir(folder) as entries:
                    foldersRead += 1
                    for entry in entries:
                        try:
                            isFolder = entry.is_dir(follow_symlinks=False)
                        except OSError as e:
                            log.debug("Could not tell if %s is a folder, skipping it: %s", entry.path, e)
                            foldersSkipped += 1
                            continue
                        if not isFolder:
                            filesFound += 1
                            yield entry
                        elif (depth < self.MAX_SCAN_DEPTH and entry.name.lower() not in self.SKIP_FOLDERS and not self.isLinkedFolder(entry)):
                            stack.append((entry.path, depth + 1))
                        else:
                            log.debug("Not descending into %s, it is too deep, a system folder or a link", entry.path)
                            foldersSkipped += 1
            except PermissionError:
                log.debug("No permission to read %s, skipping it", folder) # locked folder
                foldersSkipped += 1
                continue
            except OSError as e:
                log.warning("Skipping %s: %s", folder, e) # unreadable
                foldersSkipped += 1
        log.debug("Walked %s, read %s folders, found %s files, skipped %s folders", root, foldersRead, filesFound, foldersSkipped)


    def withinScanBudget(self, root: Path) -> tuple[bool, int]:
        """
        Counts the files under root, giving up as soon as it passes MAX_SCAN_FILES.
        """
        log.debug("Counting the files under %s, the budget is %s", root, f"{self.MAX_SCAN_FILES:,}")
        seen = 0
        for _ in self.walkFiles(root):
            seen += 1
            if seen > self.MAX_SCAN_FILES:
                log.info("%s went over the %s file budget, giving up on counting it", root, f"{self.MAX_SCAN_FILES:,}")
                return False, seen
        log.debug("%s holds %s files, within budget", root, f"{seen:,}")
        return True, seen


    def loadPCFolderContent(self) -> dict[str, set[int]]:
        """
        Fills self.pcFolderContent with the media under self.pcFiles.
        """
        if not self.pcFiles:
            log.error("loadPCFolderContent called before a destination was set")
            raise RuntimeError("No destination set, call setDestination() first.")
        log.info("Reading the media already in %s", self.pcFiles)
        self.pcFolderContent = {}
        mediaFound = 0
        notMedia = 0
        unreadable = 0
        for entry in self.walkFiles(Path(self.pcFiles)):
            if not isMedia(entry.name):
                notMedia += 1
                continue
            try:
                size = entry.stat().st_size
            except OSError as e:
                log.warning("Could not read the size of %s, leaving it out of the comparison: %s", entry.path, e)
                unreadable += 1
                continue
            mediaFound += 1
            self.pcFolderContent.setdefault(entry.name.lower(), set()).add(size)
        log.info("Found %s media files under %s (%s non media files skipped, %s unreadable)", mediaFound, self.pcFiles, notMedia, unreadable)
        return self.pcFolderContent