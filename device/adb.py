import subprocess
import shlex # shell lexicon

# learn how to use *args and **kwargs when making this if possible

class ADB():
    """wrapper around the adb command line so we can interact with the device easily."""

    headFolder = ["adb", "shell", "ls"]

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
