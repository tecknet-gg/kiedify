import queue
import subprocess
import sys
import threading
import time
import os
import shutil


class Preprocessor:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music", targetDir="/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated"):
        self.processQueue = queue.Queue()
        self.dir = dir
        self.rawDir = os.path.join(dir,"Raw")
        self.targetDir = targetDir



    def separateTrack(self, inputPath, outputDir):
        timeStart = time.perf_counter()

        try:
            subprocess.run([sys.executable, "-m", "demucs", "--mp3", "--mp3-bitrate", "320", "--two-stem=vocals", "-o", outputDir, inputPath], check=True)
        except Exception as e:
            print(e)
        timeElapsed = time.perf_counter() - timeStart

        return timeElapsed

    def generateQueue(self):
        filesPath, queuePath, targetPath = "", os.path.join(self.rawDir,"Queue"), ""
        os.makedirs(queuePath, exist_ok=True)

        recovered = 0
        for file in os.listdir(queuePath):
            if not(file.endswith(".mp3")):
                continue

            filePath = os.path.join(queuePath, file)
            name = os.path.basename(filePath)
            name, ext = os.path.splitext(name)


            if "?" in name:
                songName, artist = name.rsplit("?", 1)
            else:
                pass
                #delete file

            targetPath = os.path.join(self.dir, "Isolated", artist)
            self.processQueue.put((filePath, targetPath, artist))
            recovered += 1

        print("Recovered", recovered)

        for root, dirs, files in os.walk(self.rawDir):

            if "Queue" in root:
                continue

            for file in files:
                if not(file.endswith(".mp3")):
                    continue

                movePath = ""
                filePath = os.path.join(root, file)
                print(f"File: {filePath}")

                artist = os.path.relpath(filePath, self.rawDir)
                artist = artist.split(os.sep)[0]
                artist = artist.replace("?", "").strip()  # so it doesn't break if artists' name has a ?

                name, ext = os.path.splitext(file)
                newName = f"{name}?{artist}{ext}"

                movePath = os.path.join(queuePath, newName)

                newPath = shutil.move(filePath, movePath)

                targetPath = os.path.join(self.dir, "Isolated", artist)
                print(f"Target: {targetPath}")

                item = [newPath, targetPath, artist]
                self.processQueue.put(item)


    def process(self):
        while True:

            try:
                filePath, targetPath, artist = self.processQueue.get(timeout=1)
            except queue.Empty:
                return

            try:
                os.makedirs(targetPath, exist_ok=True)
                elapsedTime = self.separateTrack(filePath, targetPath)

                songName = os.path.basename(filePath).rsplit(".mp3", 1)[0]
                songName, _ = songName.rsplit("?", 1)

                print(f"Processing: {songName}")

                demucsOutputDir = os.path.join(targetPath, "htdemucs", songName)
                finalOutputDir = os.path.join(self.dir, "Processed", artist)
                os.makedirs(finalOutputDir, exist_ok=True)

                vocalStem = os.path.join(demucsOutputDir, "vocals.mp3")

                if os.path.exists(vocalStem):
                    destination = os.path.join(finalOutputDir, f"{songName}.mp3")
                    shutil.move(vocalStem, destination)

            except Exception as e:
                print(e)
            finally:

                if os.path.exists(filePath):
                    os.remove(filePath)

                print(f"Finished processing {songName} in {elapsedTime} seconds")
                self.processQueue.task_done()


    def processMulithreaded(self, nthread=4):
        threads = []
        for i in range(nthread):
            thread = threading.Thread(target=self.process)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return True


    def cleanRaw(self):
        # clean raw of empty folders
        pass




if __name__ == "__main__":
    inputPath = "/Users/jeevan/Documents/Python/MusicTTS/Music/Green Day/American Idiot/American Idiot.mp3"
    outputDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated/Paramore"
    preprocessor = Preprocessor()
    preprocessor.generateQueue()
    preprocessor.processMulithreaded(nthread=4)
