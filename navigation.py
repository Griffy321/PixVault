import subprocess

class FileNavigation():
    """Handles filesystem navigation on an Android device over ADB."""
    
    head = "/sdcard"
    pictures = "/sdcard/Pictures"

    def __init__(self):
        pass

    def toHeadDir(self):
        """
        returns all the folders at the top level of the phone 
        """
        result = subprocess.run(["adb", "shell", "ls", self.head], capture_output=True, text=True)
        return result.stdout.strip().splitlines()

    # def buildPath(self, folderName):
    #     """Constructs an absolute path string by appending a folder name to the base directory."""
    #     finalPath = ""
    #     pass

    # def toPictures(self):
    #     """
    #     returns all the file names in the pictures folder
    #     """
    #     result = subprocess.run(["adb", "shell", "ls", self.pictures], capture_output=True, text=True)
    #     return result.stdout.strip().splitlines()

    def loadFiles(self):
        """Loads files from the device into memory for further processing."""
        pass

    def returnFiles(self):
        """Returns the currently loaded list of files."""
        pass

    def searchFiles(self, query, path=None):
        """
        Recursively searches the ADB filesystem under `path` (defaults to /sdcard)
        for files whose names match `query`. Supports wildcard patterns (e.g. *.jpg)
        and substring matches. Returns a list of matching absolute file paths.
        Handles permission-denied errors gracefully by skipping inaccessible directories.
        """
        pass

    def listDir(self, path):
        """
        Lists the contents of any directory on the device at the given `path`.
        Parses `adb shell ls -la` output to return structured data per entry,
        including name, type (file/directory), size, and last-modified date.
        """
        pass

    def getFileMetadata(self, path):
        """
        Returns metadata for a single file or directory at `path` on the device.
        Uses `adb shell stat` to retrieve size, permissions, and last-modified
        timestamp. Useful for detecting whether a file has already been backed up.
        """
        pass

    def findMediaDirs(self):
        """
        Probes a list of known Android media locations (e.g. /sdcard/DCIM,
        /sdcard/Pictures, /sdcard/WhatsApp/Media/WhatsApp Images) and returns
        only those that actually exist on the connected device. Intended as a
        discovery step before presenting photos in the swipe UI.
        """
        pass

nav = FileNavigation()

print(nav.buildPath())