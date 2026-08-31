import subprocess
import shlex # shell lexicon
import sys
from pathlib import Path
from shutil import which

from config import isMedia
from pvlogging import getLogger

log = getLogger(__name__)

# learn how to use *args and **kwargs when making this if possible


def resolveADBPath() -> str:
    """Finds the adb executable to use, preferring the copy bundled with the app
    over one the user may have installed themselves, falling back to PATH."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller build: bundled files live under sys._MEIPASS.
        bundled = Path(sys._MEIPASS) / "platform-tools" / "adb.exe"
    else:
        bundled = Path(__file__).resolve().parent.parent / "vendor" / "platform-tools" / "adb.exe"
    if bundled.is_file():
        return str(bundled)
    log.warning("Bundled adb not found at %s, falling back to PATH", bundled)
    onPath = which("adb")
    if onPath:
        return onPath
    raise FileNotFoundError("Could not find adb, neither bundled nor on PATH")


class ADB():
    """Wrapper around the adb command line so we can interact with the device easily."""

    def __init__(self):
        adbPath = resolveADBPath()
        self.headFolder = [adbPath, "shell", "ls"]
        self.pullFrom = [adbPath, "pull"]
        self.headFolderSizes = [adbPath, "shell", "ls", "-l"]
        self.adbPath = adbPath


    def isDeviceConnected(self):
        """Returns True if exactly one authorised device is visible to ADB."""
        output = subprocess.run([self.adbPath, "devices"], capture_output=True, text=True)
        deviceID = output.stdout.replace("List of devices attached", "").replace("device", "").strip()
        if len(deviceID) >= 10: # check to make sure we've not picked up some random word
            log.info("Device connected: %s", deviceID)
            return [True, deviceID]
        log.warning("No device found, adb devices gave back: %s", deviceID or "nothing")
        return [False, deviceID]


    def fromHeadDir(self, path):
        """Navigates down from the relitive top of the file directory to where the user specifies"""
        log.debug("Listing %s", path)
        result = subprocess.run(self.headFolder + [shlex.quote(path)], capture_output=True, text=True)
        if result.returncode != 0:
            log.error("Could not list %s, error code %s: %s", path, result.returncode, result.stderr.strip())
        return result.stdout.strip().splitlines()


    def pullFiles(self, remotePath: str, localPath: str) -> bool:
        """Copies one file off the device with `adb pull`, returning True on success and false on a fail"""
        command = self.pullFrom + [remotePath, localPath]
        log.debug("Pulling %s into %s", remotePath, localPath)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            log.error("Failed to pull %s into %s, error code %s: %s", remotePath, localPath, result.returncode, result.stderr.strip())
            return False
        log.info("Pulled %s", remotePath)
        return True


    def backupDict(self, path: str) -> dict[str, int]:
        """Returns {filename: bytes} for everything in path"""
        toBackup = {}
        command = self.headFolderSizes + [shlex.quote(path)]
        log.debug("Sizing up the contents of %s", path)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            log.error("Could not read %s, error code %s: %s", path, result.returncode, result.stderr.strip())
            raise TypeError("File path not found")
        outputs = result.stdout.split("\n")[1:-1]
        outputItems = [output.split() for output in outputs]
        for data in outputItems:
            fileName = " ".join(data[7:])
            if not isMedia(fileName):
                log.debug("'%s' does not appear to be media, skipping.", fileName)
                continue
            try:
                size = int(data[4]) # in bytes
            except Exception:
                log.warning("Failed to get size for %s, trying to fetch single file", fileName)
                size = self.singleFileSize(path, fileName)
            toBackup[fileName] = size
        if len(toBackup) == 0:
            log.warning("No media files found in %s", path)
            raise FileNotFoundError("No media files in this destination")
        log.info("Found %s media files in %s", len(toBackup), path)
        return toBackup


    def singleFileSize(self, path:str, file: str) -> int:
        """A backup function for self.backupDict that will get the bytes of a file if self.backupDict has an issue getting the bytes"""
        command = self.headFolderSizes + [shlex.quote(path + "/" + file)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            log.error("Could not read %s/%s, error code %s: %s", path, file, result.returncode, result.stderr.strip())
            raise TypeError("File not found")
        output = result.stdout.split()
        try:
            size = int(output[4]) # in bytes
        except Exception:
            log.warning("Still could not read a size for %s, recording it as 0 bytes", file)
            size = 0 # accept defeat
        return size