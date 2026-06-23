import pathlib
import time

while True:
    filePath = input("Please enter a file path >")
    pathExists = pathlib.Path(filePath).exists()
    if pathExists == True:
        print("The file exists, fetching data...")
        time.sleep(3) # makes it look like it's doing something 
        
    else:
        print("Ran into error - try a different path please")