import subprocess

class FileNavigation():
    """Handles filesystem navigation on an Android device over ADB."""
    
    sdCardFolder = "adb/shell/ls/sdcard"


    def __init__(self):
        pass


    def fromHeadDir(self, path=None):
        """
        navigates down from the relitive top of the file directory to where the user specifies
        """
        if path is None:
            result = subprocess.run(self.sdCardFolder.split("/"), capture_output=True, text=True)
        if path is not None:
            combinedPath = self.sdCardFolder.split("/") 
            combinedPath[-1] = combinedPath[-1] + path
            result = subprocess.run(combinedPath, capture_output=True, text=True)
        return result.stdout.strip().splitlines()


    def toFiles(self): # we will try this if we have files selected
        """
        Loads files from the device into memory for further processing.
        """
        # adb = android debug bridge
        result = subprocess.run(self.sdCardFolder.split("/"), capture_output=True, text=True)
        return result.stdout.strip().splitlines()


    def buildPath(self):
        """Constructs an absolute path string by appending a folder name to the base directory."""
        finalPath = ""
        keepExploring = True
        while keepExploring:
            nextStep = input("Please enter the next folder you want to navigate to: ")
            if nextStep.lower() == "stop":
                return positition
            
            finalPath += "/" + nextStep
            positition = self.fromHeadDir(path=finalPath)
            print(positition)
        return positition


    def returnFiles(self):
        """Returns the currently loaded list of files."""
        pass

print(FileNavigation().toFiles())
print(FileNavigation().buildPath())

