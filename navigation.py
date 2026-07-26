import subprocess

# TODO LIST — keep this simple. The only job is: reach a folder, then hand its
# images/videos to the swipe view. Anything beyond that is out of scope.
#
# 4. listFolders() vs listMediaFiles() — split the ls output into subfolders and
#    media files (.jpg/.jpeg/.png/.heic/.mp4/.mov). Folders are what you navigate
#    into; media files are what you stop at and pass to the swipe view.
#
# 5. Validate the folder exists before entering it. Right now a typo just returns
#    an empty list and looks the same as an empty folder.
#
# 6. Build commands as a real list (["adb", "shell", "ls", path]) instead of
#    splitting a string on "/" — folder names with spaces break the current way.


class FileNavigation():
    """Handles filesystem navigation on an Android device over ADB."""

    headFolder = "adb/shell/ls"


    def __init__(self):
        # Path segments, top-level first. Joined on demand by currentPath().
        self.currentLocation = ["sdcard"]


    def isDeviceConnected(self):
        """Returns True if exactly one authorised device is visible to ADB."""
        output = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        deviceID = output.stdout.replace("List of devices attached", "").replace("device", "").strip()

        if len(deviceID) >= 10: # check to make sure we've not picked up some random word
            return [True, deviceID]
        return [False, deviceID]


    def goBack(self):
        """Steps up one folder, stopping at /sdcard."""
        if len(self.currentLocation) == 1:
            print("You are already at the top folder, please navigate down from here")
        else:
            self.currentLocation.pop(-1)
            print(f"You went back, the new current location is : {self.currentPath()}")


    def currentPath(self):
        """Returns the current location as a printable path string."""
        return "/".join(self.currentLocation)


    # TODO: implement — see item 4 above
    def listFolders(self):
        """Returns just the subfolders at the current location."""
        pass


    # TODO: implement — see item 4 above
    def listMediaFiles(self):
        """Returns just the images/videos at the current location."""
        pass


    def fromHeadDir(self, path):
        """
        navigates down from the relitive top of the file directory to where the user specifies
        """
        startingPath = self.headFolder.split("/") 
        result = subprocess.run(startingPath + [path], capture_output=True, text=True)
        return result.stdout.strip().splitlines()


    def toFiles(self): # we will try this if we have files selected
        """
        Loads files from the device into memory for further processing.
        """
        result = subprocess.run(self.headFolder.split("/") + ["sdcard"], capture_output=True, text=True)
        return result.stdout.strip().splitlines()


    def buildPath(self):
        """Constructs an absolute path string by appending a folder name to the base directory."""
        # check if device is connected
        deviceConnected = self.isDeviceConnected()
        if deviceConnected[0]:
            print(f"Device successfully connected! ID : {deviceConnected[1]}")
        else:
            raise RuntimeError(f"Unable to detect a connected device, please connect or check the connection of your device \n{deviceConnected}")

        while True:
            # List first, so position is always bound and always matches where we are.
            position = self.fromHeadDir(path=self.currentPath())
            print(f"\nCurrent location: {self.currentPath()}")
            print(position)

            nextStep = input("Please enter the next folder you want to navigate to: ")
            if nextStep.lower() == "stop":
                return position
            elif nextStep.lower() == "back":
                self.goBack()
            else:
                self.currentLocation.append(nextStep) # add check on curent path here