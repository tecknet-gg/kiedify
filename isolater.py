import queue
import subprocess
import sys
import threading
import time
import os
import json
import shutil
from directory import DirectoryManager

class Preprocessor:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.processQueue = queue.Queue()
        self.dir = dir
        self.rawDir = os.path.join(dir,"Raw")
        self.targetDir = os.path.join(dir, "Isolated")
        self.manager = DirectoryManager(dir)

        self.manifestLock = threading.Lock()

    def separateTrack(self, inputPath, outputDir):
        timeStart = time.perf_counter()

        try:
            subprocess.run([sys.executable, "-m", "demucs", "--mp3", "--mp3-bitrate", "320", "--two-stem=vocals", "-o", outputDir, inputPath], check=True)
        except Exception as e:
            print(e)
        timeElapsed = time.perf_counter() - timeStart

        return timeElapsed

    def generateQueue(self):
        recovered = 0

        for root, dirs, files in os.walk(self.rawDir):
            for file in files:
                if file.endswith(".json"):
                    jsonPath = os.path.join(root, file)

                    try:
                        with open(jsonPath, "r") as f:
                            tracks = json.load(f)
                    except Exception as e:
                        print(f"Failed to load {jsonPath}: error: {e}")
                        continue

                    for track in tracks:
                        title = track["title"]
                        artist = track["artist"]
                        album = track["album"]

                        albumDir = os.path.dirname(jsonPath)
                        mp3Path = os.path.join(albumDir, f"{title}.mp3")

                        if os.path.exists(mp3Path):
                            self.processQueue.put((mp3Path, title, artist, album))
                            recovered += 1
                        else:
                            print(f"Missing file for {title}")

        print(f"Added: {recovered}")

    def process(self):
        while True:

            try:
                filePath, songName, artist, album = self.processQueue.get(timeout=1)
            except queue.Empty:
                return

            elapsedTime = 0

            try:
                isolationTargetDir = os.path.join(self.dir, "Isolated", artist)
                os.makedirs(isolationTargetDir, exist_ok=True)

                print(f"Processing: {songName}")
                elapsedTime = self.separateTrack(filePath, isolationTargetDir)

                rawFolderName = os.path.splitext(os.path.basename(filePath))[0]
                demucsOutputDir = os.path.join(isolationTargetDir, "htdemucs", rawFolderName)

                finalOutputDir = os.path.join(self.dir, "Processed", artist, album)
                os.makedirs(finalOutputDir, exist_ok=True)

                sourceJson = os.path.join(os.path.dirname(filePath), f"{album}.json")
                destJson = os.path.join(finalOutputDir, f"{album}.json")


                vocalStem = os.path.join(demucsOutputDir, f"vocals.mp3")

                if os.path.exists(vocalStem):
                    destination = os.path.join(finalOutputDir, f"{songName}.mp3")
                    shutil.move(vocalStem, destination)
                    print(f"Moved {songName}.mp3 to {destination}")

                    if os.path.exists(sourceJson):
                        try:
                            with self.manifestLock:
                                with open(sourceJson, "r") as f:
                                    originalTracks = json.load(f)
                                currentTracks = next((t for t in originalTracks if t['title'] == songName), None)

                                if currentTracks:
                                    processedTracks = []

                                if os.path.exists(destJson):
                                    try:
                                        with open(destJson, "r") as f:
                                            processedTracks = json.load(f)

                                    except Exception as e:
                                        print(f"Failed to load {destJson}: error: {e}")
                                        return

                                if currentTracks not in processedTracks:
                                    processedTracks.append(currentTracks)

                                with open(destJson, "w") as f:
                                    json.dump(processedTracks, f, indent=4)

                        except Exception as e:
                            print(f"Failed to save {destJson}: error: {e}")

                        try:
                            os.remove(filePath)
                        except Exception as e:
                            print(f"Failed to remove {filePath}: {e}")

                else:
                    print(f"Missing file for {songName}")

            except Exception as e:
                print(f"Failed to process {songName}: {e}")


            print(f"Finished processing {songName} in {round(elapsedTime, 2)} seconds")

            self.processQueue.task_done()

    def processMulithreaded(self, nthread=1):
        threads = []
        for i in range(nthread):
            thread = threading.Thread(target=self.process)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return True



if __name__ == "__main__":

    preprocessor = Preprocessor()
    preprocessor.generateQueue()
    preprocessor.processMulithreaded(nthread=4)

    manager = DirectoryManager()
    manager.cleanDownloadDir()
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()
