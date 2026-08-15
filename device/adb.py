import subprocess
import shlex # shell lexicon

from config import isMedia

# learn how to use *args and **kwargs when making this if possible

class ADB():
    """Wrapper around the adb command line so we can interact with the device easily."""

    headFolder = ["adb", "shell", "ls"]
    pullFrom = ["adb", "pull"]
    headFolderSizes = ["adb", "shell", "ls", "-l"]

    def __init__(self):
        pass

    def isDeviceConnected(self):
        """Returns True if exactly one authorised device is visible to ADB."""
        output = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        deviceID = output.stdout.replace("List of devices attached", "").replace("device", "").strip()

        if len(deviceID) >= 10: # check to make sure we've not picked up some random word
            return [True, deviceID]
        return [False, deviceID]

    def fromHeadDir(self, path):
        """Navigates down from the relitive top of the file directory to where the user specifies"""
        result = subprocess.run(self.headFolder + [shlex.quote(path)], capture_output=True, text=True)
        return result.stdout.strip().splitlines()

    def pullFiles(self, remotePath: str, localPath: str) -> bool:
        """Copies one file off the device with `adb pull`, returning True on success and false on a fail"""
        command = self.pullFrom + [remotePath, localPath]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to pull file - {remotePath} - into - {localPath}\nError code: {result.returncode} \nError msg: {result.stderr}")
            return False
        return True

    def backupDict(self, path: str) -> dict[str, int]:
        """Returns {filename: bytes} for everything in path"""
        toBackup = {}
        command = self.headFolderSizes + [shlex.quote(path)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise TypeError("File path not found")
        outputs = result.stdout.split("\n")[1:-1]
        outputItems = [output.split() for output in outputs]
        for data in outputItems:
            fileName = " ".join(data[7:])
            if not isMedia(fileName):
                print(f"'{fileName}' does not appear to be media, skipping.")
                continue
            try:
                size = int(data[4]) # in bytes
            except Exception:
                print(f"Failed to get size for {fileName}, trying to fetch single file")
                size = self.singleFileSize(path, fileName)
            toBackup[fileName] = size

        if len(toBackup) == 0:
            raise FileNotFoundError("No media files in this destination")
        return toBackup

    def singleFileSize(self, path:str, file: str) -> int:
        """A backup function for self.backupDict that will get the bytes of a file if self.backupDict has an issue getting the bytes"""
        command = self.headFolderSizes + [shlex.quote(path + "/" + file)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise TypeError("File not found")
        output = result.stdout.split()
        try:
            size = int(output[4]) # in bytes
        except Exception:
            size = 0 # accept defeat
        return size