import subprocess

from device.adb import ADB


class FileSaving:

    """Class to handle photo and video saving from one device to the other"""

    def __init__(self):
        self.adb = ADB()


    def toFiles(self): # we will try this if we have files selected
        """
        Loads files from the device into memory for further processing.
        """
        result = subprocess.run(self.adb.headFolder.split("/") + ["sdcard"], capture_output=True, text=True)
        return result.stdout.strip().splitlines()
