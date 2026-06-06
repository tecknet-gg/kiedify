import queue
import subprocess
import sys
import time
import os
import shutil


class Preprocessor:
    def __init__(self, rawDir="/Users/jeevan/Documents/Python/MusicTTS/Music/Raw", targetDir="/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated"):
        self.processQueue = queue.Queue()
        self.rawDir = rawDir
        self.targetDir = targetDir

    def separateTrack(self, inputPath, outputDir):
        subprocess.run([sys.executable, "-m", "demucs", "-o", outputDir, inputPath], check=True)

    def generateQueue(self):
        filesPath, queuePath, targetPath = "", os.path.join(self.rawDir,"Queue"), ""
        os.makedirs(queuePath, exist_ok=True)
        for root, dirs, files in os.walk(self.rawDir):
            for file in files:
                if not(file.endswith(".mp3")):
                    continue

                movePath = ""
                filePath = os.path.join(root, file)
                print(f"File: {filePath}")

                movePath = os.path.join(queuePath, file)
                artist = (filePath.split("Raw/")[1]).split("/")[0]

                shutil.move(filePath, movePath)

                targetPath = os.path.join(root, "Isolated", artist, file)
                print(f"Target: {targetPath}")

                item = [filePath, targetPath, artist]
                self.processQueue.put(item)

    def cleanRaw(self):
        pass




if __name__ == "__main__":
    inputPath = "/Users/jeevan/Documents/Python/MusicTTS/Music/Green Day/American Idiot/American Idiot.mp3"
    outputDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated/Paramore"
    preprocessor = Preprocessor()
    preprocessor.generateQueue()
