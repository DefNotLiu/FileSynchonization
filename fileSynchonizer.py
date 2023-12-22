import os
import shutil
import filecmp
import signal
import time
import hashlib
from datetime import datetime

#buffer size of reading files
BUFFER_SIZE = 4096
#conditional variabel for signal handler
forceExit = False

def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        print("Program will exit after finishing the operations")
        global forceExit
        forceExit= True

def writeConsolAndLog(logFD, msg):
    logFD.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + msg + "\n")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + msg)

#walk through original directory
def scanDirectory(originalLocation, logFile):
    originalFiles = {}
    originalFolders = {}
    #writeConsolAndLog(logFile, "Info - Scanning Original directory.")
    
    for root, dirs, files in os.walk(originalLocation, topdown=True):
        tmp = root[len(originalLocation)+1:]
        for name in files:
            #writeConsolAndLog(logFile, "Info - " + os.path.join(root, name) + " found.")
            originalFiles[os.path.join(tmp, name)] = False
        for name in dirs:
            #writeConsolAndLog(logFile, "Info - " + os.path.join(root, name) + " found.")
            originalFolders[os.path.join(tmp, name)] = False

    return originalFiles, originalFolders

#walk through duplicate, remove files not present in original and mark those present
def scanDirectoryAndRemove(originalLocation, originalFiles, originalFolders, duplicateLocation, logFile, useHash):
    #writeConsolAndLog(logFile, "Info - Scanning Duplicate directory.")
    for root, dirs, files in os.walk(duplicateLocation, topdown=False):
        tmp = root[len(duplicateLocation)+1:]
        for name in files:
            dupFile = os.path.join(tmp, name)
            #full path of files
            dupFullFile = os.path.join(duplicateLocation, dupFile)
            oriFullFile = os.path.join(originalLocation, dupFile)
            if dupFile not in originalFiles:
                writeConsolAndLog(logFile, "Removing " + os.path.join(root, name))
                os.remove(dupFullFile)
            #compare content
            elif not useHash:
                if filecmp.cmp(dupFullFile, oriFullFile, True):
                    #writeConsolAndLog(logFile, "Info - " + os.path.join(root, name) + " found in Original directory.")
                    originalFiles[dupFile] = True
                else:
                    writeConsolAndLog(logFile, "Removing " + os.path.join(root, name))
                    os.remove(dupFullFile)
            #compare hash
            else:
                if calculateMd5(dupFullFile) == calculateMd5(oriFullFile):
                    #writeConsolAndLog(logFile, "Info - " + os.path.join(root, name) + " found in Original directory.")
                    originalFiles[dupFile] = True
                else:
                    writeConsolAndLog(logFile, "Removing " + os.path.join(root, name))
                    os.remove(dupFullFile)
        for name in dirs:
            dupDir = os.path.join(tmp, name)
            if dupDir not in originalFolders:
                writeConsolAndLog(logFile, "Removing " + os.path.join(root, name))
                os.rmdir(os.path.join(duplicateLocation, dupDir))
            else:
                #writeConsolAndLog(logFile, "Info - " + os.path.join(root, name) + " found in Original directory.")
                originalFolders[dupDir] = True

#copy rest of the files non marked in original
def copyUnexistentFiles(originalLocation, originalFiles, duplicateLocation, logFile):
    for file in originalFiles:
        if not originalFiles[file]:
            oriJoinedLoc = os.path.join(originalLocation, file)
            dupJoinedLoc = os.path.join(duplicateLocation, file)
            try:
                writeConsolAndLog(logFile, "Copying " + oriJoinedLoc)
                shutil.copyfile(oriJoinedLoc, dupJoinedLoc)
            except FileNotFoundError:
                writeConsolAndLog(logFile, "Creating directory " + dupJoinedLoc[:dupJoinedLoc.rfind("\\")])
                os.makedirs(dupJoinedLoc[:dupJoinedLoc.rfind("\\")])
                writeConsolAndLog(logFile, "Copying " + oriJoinedLoc)
                shutil.copyfile(oriJoinedLoc, dupJoinedLoc)
            except PermissionError:
                writeConsolAndLog(logFile, "Warning - Permission denied.")

#calculate hash
def calculateMd5(filePath):
    md5 = hashlib.md5()
    with open(filePath, "rb") as file:
        while True:
            data = file.read(BUFFER_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def readInput():

    originalLocation = ""
    duplicateLocation = ""
    logLocation = ""
    syncInterval = -1
    useHash = True

    while os.path.exists(originalLocation) == False:
        originalLocation = input("Insert original directory\n")
    while os.path.exists(duplicateLocation) == False:
        duplicateLocation = input("Insert duplicate directory\n")
    while os.path.exists(logLocation) == False:
        logLocation = input("Insert log file directory\n")
    while syncInterval <= 0:
        try:
            syncInterval = int(input("Insert time interval in seconds\n"))
        except ValueError:
            print("Incorrect interval, insert time interval in seconds")
    
    if input("Compare the content of the files precisely? y/n\n")=='y':
        useHash = False

    return originalLocation, duplicateLocation, logLocation, syncInterval, useHash

def main():

    originalLocation, duplicateLocation, logLocation, syncInterval, useHash = readInput()

    """print(originalLocation)
    print(duplicateLocation)
    print(syncInterval)
    print(logLocation)
    print(useHash)"""

    logFile = open(os.path.join(logLocation, "log.txt"),"w")

    while not forceExit:
        
        #scan original directory and retrieve files and folders
        originalFiles, originalFolders = scanDirectory(originalLocation, logFile)

        #scan duplicate and remove those not present in original and marking the same files
        scanDirectoryAndRemove(originalLocation, originalFiles, originalFolders, duplicateLocation, logFile, useHash)

        #print(originalFiles)
        #print(originalFolders)

        #copy the nonmarked files
        copyUnexistentFiles(originalLocation, originalFiles, duplicateLocation, logFile)

        time.sleep(syncInterval)
        
    writeConsolAndLog(logFile, "Closing log")
    logFile.close()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    main()