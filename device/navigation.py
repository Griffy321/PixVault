from device.adb import ADB

# TODO LIST — keep this simple. The only job is: reach a folder, then hand its
# images/videos to the swipe view. Anything beyond that is out of scope.
#
# 4. listFolders() vs listMediaFiles() — split the ls output into subfolders and
#    media files (.jpg/.jpeg/.png/.heic/.mp4/.mov). Folders are what you navigate
#    into; media files are what you stop at and pass to the swipe view.
#
# 5. Validate the folder exists before entering it. Right now a typo just returns
#    an empty list and looks the same as an empty folder.


class FileNavigation():
    """Handles filesystem navigation on an Android device using the ADB."""

    def __init__(self):
        # Path segments, top-level first - joined on demand by currentPath().
        self.currentLocation = ["sdcard"]
        self.mediaFiles = [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]
        self.adb = ADB()


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
    def listFolders(self, folderContents):
        """Returns just the subfolders at the current location."""
        # try to just use .endswith()
        # for value in folderContents:
        #     if value.endswith()
        pass


    # TODO: implement — see item 4 above
    def listMediaFiles(self, folderContents:list):
        """Returns just the images/videos at the current location."""
        # files = []
        # for value in folderContents:
        #     if value.endswith(self.mediaFiles.__getitem__):
        #         files.append(value)
        # return files
        pass


    def buildPath(self):
        """Constructs an absolute path string by appending a folder name to the base directory."""
        # check if device is connected
        deviceConnected = self.adb.isDeviceConnected()
        if deviceConnected[0]:
            print(f"Device successfully connected! ID : {deviceConnected[1]}")
        else:
            raise RuntimeError(f"Unable to detect a connected device, please connect or check the connection of your device \n{deviceConnected}")

        while True:
            # List first, so position is always bound and always matches where we are.
            position = self.adb.fromHeadDir(path=self.currentPath())
            print(f"\nCurrent location: {self.currentPath()}")
            print(position)
            print(self.listMediaFiles(position))
            nextStep = input("Please enter the next folder you want to navigate to: ")
            if nextStep.lower() == "stop":
                return position
            elif nextStep.lower() == "back":
                self.goBack()
            else:
                self.currentLocation.append(nextStep) # add check on curent path here
