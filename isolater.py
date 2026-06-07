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
        filesPath, queuePath, targetPath = "", os.path.join(self.rawDir,"Queue"), ""
        os.makedirs(queuePath, exist_ok=True)

        recovered = 0
        for file in os.listdir(queuePath):
            if not(file.endswith(".mp3")):
                continue

            filePath = os.path.join(queuePath, file)
            name = os.path.basename(filePath)
            name, ext = os.path.splitext(name)


            if "||" in name:
                songName, artist = name.rsplit("||", 1)
            else:
                pass
                #delete file

            targetPath = os.path.join(self.dir, "Isolated", artist)
            self.processQueue.put((filePath, targetPath, artist))
            recovered += 1

        print("Added", recovered)

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
                artist = artist.replace("||", "").strip()  # so it doesn't break if artists' name has a ||

                name, ext = os.path.splitext(file)
                newName = f"{name}||{artist}{ext}"

                movePath = os.path.join(queuePath, newName)

                newPath = shutil.move(filePath, movePath)

                targetPath = os.path.join(self.dir, "Isolated", artist)
                print(f"Target: {targetPath}")

                item = [newPath, targetPath, artist]
                self.processQueue.put(item)


        pass

    def generateQueue2(self):
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

                                if currentTracks not in processedTracks:
                                    processedTracks.append(currentTracks)

                                with open(destJson, "w") as f:
                                    json.dump(processedTracks, f, indent=4)

                        except Exception as e:
                            print(f"Failed to save {destJson}: error: {e}")

                else:
                    print(f"Missing file for {songName}")

            except Exception as e:
                print(f"Failed to process {songName}: {e}")


            print(f"Finished processing {songName} in {round(elapsedTime, 2)} seconds")
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

    def cleanDir(self):
        isolatedRoot = self.targetDir

        if os.path.exists(isolatedRoot):
            for root, dirs, files in os.walk(isolatedRoot, topdown=False):
                if "htdemucs" in root and root != (os.path.join(isolatedRoot, "htdemucs")):
                    if "vocals.mp3" not in files:
                        try:
                            shutil.rmtree(root)
                            print(f"Removed {root}")
                        except Exception as e:
                            print(f"Failed to remove {root}: {e}")
            for root, dirs, files in os.walk(isolatedRoot, topdown=False):
                if root != isolatedRoot and not os.listdir(root):
                    try:
                        os.rmdir(root)
                        print(f"Removed {root}")
                    except Exception as e:
                        print(f"Failed to remove {root}: {e}")

        if os.path.exists(self.rawDir):
            for root, dirs, files in os.walk(self.rawDir, topdown=False):
                if root == self.rawDir:
                    continue

                if not os.listdir(root):
                    try:
                        os.rmdir(root)
                        print(f"Removed {root}")
                    except Exception as e:
                        print(f"Failed to remove {root}: {e}")

        print("Cleanup finished.")


    def flattenDir(self):
        processedRoot = os.path.join(self.dir, "Processed")
        if not os.path.exists(processedRoot):
            print("Directory missing")
            return

        for artist in os.listdir(processedRoot):
            artistPath = os.path.join(processedRoot, artist)
            if not os.path.isdir(artistPath):
                continue

            artistManifestPath = os.path.join(ArtistPath, f"{artist}.json")
            allArtistTracks = []

            for album in os.listdir(artistPath):
                albumPath = os.path.join(artistPath, album)

                if os.path.isdir(albumPath):
                    albumJsonPath = os.path.join(albumPath, f"{album}.json")
                    if os.path.exists(albumJsonPath):
                        try:
                            with open(albumJsonPath, "r") as f:
                                tracks = json.load(f)
                                for track in tracks:
                                    if track not in allArtistTracks:
                                        allArtistTracks.append(track)
                        except Exception as e:
                            print(f"Failed to load {albumJsonPath}: error: {e}")

                    for root, dirs, files in os.walk(albumPath, topdown=False):
                        for file in files:
                            if file.endswith(".json"):
                                continue

                            currentFilePath = os.path.join(root, file)
                            targetFilePath = os.path.join(artistPath, file)

                            try:
                                shutil.move(currentFilePath, targetFilePath)
                                print(f"Moved {currentFilePath} to {targetFilePath}")
                            except Exception as e:
                                print(f"Failed to move {currentFilePath}: {e}")

                    try:
                        shutil.rmtree(albumPath)
                    except Exception as e:
                        print(f"Failed to remove {albumPath}: {e}")

                    if allArtistTracks:
                        if os.path.exists(artistManifestPath):
                            try:
                                with open(artistManifestPath, "r") as f:
                                    existing = json.load(f)
                                    for track in existing:
                                        if track not in allArtistTracks:
                                            allArtistTracks.append(track)
                            except Exception as e:
                                print(f"Failed to load {artistManifestPath}: error: {e}")

                        try:
                            with open(artistManifestPath, "w") as f:
                                json.dump(allArtistTracks, f, indent=4)
                            print(f"Consolidated manifest created for {artist}")
                        except Exception as e:
                            print(f"Failed to save {artistManifestPath}: error: {e}")

        pass
if __name__ == "__main__":

    preprocessor = Preprocessor()
    #preprocessor.generateQueue2()
    #preprocessor.processMulithreaded(nthread=4)
    preprocessor.cleanDir()
