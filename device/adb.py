import subprocess
import shlex # shell lexicon

# learn how to use *args and **kwargs when making this if possible

class ADB():
    """wrapper around the adb command line so we can interact with the device easily."""

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
        """
        navigates down from the relitive top of the file directory to where the user specifies
        """
        result = subprocess.run(self.headFolder + [shlex.quote(path)], capture_output=True, text=True)
        return result.stdout.strip().splitlines()

    def pullFiles(self, remotePath: str, localPath: str) -> bool:
        """
        Copies one file off the device with `adb pull`, returning True on success and false on a fail
        """
        command = self.pullFrom + [remotePath, localPath]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to pull file - {remotePath} - into - {localPath}\nError code: {result.returncode} \nError msg: {result.stderr}")
            return False
        return True

    def sizesInFolder(self, path: str) -> dict[str, int]:
        """
        Returns {filename: bytes} for everything in path, read from one `ls -l` call
        so a folder of 500 photos costs a single round trip rather than 500.
        """
        pass

    bytes_of_files_in_a_folder = """adb shell ls -l 'sdcard/DCIM/'"""