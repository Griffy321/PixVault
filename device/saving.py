from adb import ADB
from device.navigation import FileNavigation
from pathlib import Path


class FileSaving:

    """Class to handle photo and video saving from one device to the other"""

    def __init__(self):
        self.deviceFiles = ADB()
        self.pcFiles = Path()
        self.pcFolderContent = []
        self.toBackup = []

    # setting up the destination

    def setDestination(self, folder: str) -> None:
        """Points self.pcFiles at the folder the user picked, creating it if it is
        not there yet so the first pull cannot fail on a missing directory."""
        pass

    def loadFolderContent(self) -> list[str]:
        """Fills self.pcFolderContent with the filenames already in self.pcFiles.
        Read once per run so each file check is a lookup, not a fresh disk scan."""
        pass

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

    def saveAll(self) -> dict[str, str]:
        """Runs saveFile over self.toBackup and returns each file's outcome
        ("saved" / "skipped" / "failed") for the progress view to report."""
        pass

    def verifySaved(self, remotePath: str, localPath: Path) -> bool:
        """Confirms the local copy is complete after a pull, so a half-written file
        from a yanked cable is not counted as backed up."""
        pass

