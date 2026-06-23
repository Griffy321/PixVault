import subprocess

class FileNavigation():
    
    head = "/sdcard"

    def __init__(self):
        pass

    def toHeadDir(self):
        """
        returns all the folders at the top of the phone 
        """
        result = subprocess.run(["adb", "shell", "ls", self.head, "/pictures"], capture_output=True, text=True)
        return result.stdout.strip().splitlines()


nav = FileNavigation()

print(nav.toHeadDir())