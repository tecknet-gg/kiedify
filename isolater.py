import queue
import subprocess
import sys
import threading
import time
import os
import json
import shutil
from concurrent.futures import ThreadPoolExecutor

from directory import DirectoryManager

class Preprocessor:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.processQueue = queue.Queue()
        self.dir = dir
        self.rawDir = os.path.join(dir,"Raw")
        self.targetDir = os.path.join(dir, "Isolated")
        self.manager = DirectoryManager(self.dir)

        self.manifestLock = threading.Lock()

    def separateTrack(self, inputPath, outputDir):
        timeStart = time.perf_counter()

        try:
            subprocess.run([sys.executable, "-m", "demucs", "--mp3", "--mp3-bitrate", "320", "--two-stem=vocals", "-o", outputDir, inputPath], check=True)
        except Exception as e:
            print(e)
        timeElapsed = time.perf_counter() - timeStart

        return timeElapsed

    def gatherTracks(self):
        tracksToProcess = []
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
                        albumDir = os.path.dirname(jsonPath)
                        audio = os.path.join(albumDir, f"{track['title']}.mp3")

                        if os.path.exists(audio):
                            tracksToProcess.append((audio, track["title"], track["artist"], track["album"]))

        return tracksToProcess

    def processTrack(self, trackData):
        filePath, songName, artist, album = trackData
        elapsedTime = 0

        try:
            target = os.path.join(self.dir, "Isolated", artist)
            os.makedirs(target, exist_ok=True)

            print(f"Processing: {songName}")
            elapsedTime = self.separateTrack(filePath, target)

            rawFolder = os.path.splitext(os.path.basename(filePath))[0]
            demucsOutputDir = os.path.join(target, "htdemucs", rawFolder)

            finalOutputDir = os.path.join(self.dir, "Processed", artist, album)
            os.makedirs(finalOutputDir, exist_ok=True)

            sourceJson = os.path.join(os.path.dirname(filePath), f"{album}.json")
            destJson = os.path.join(finalOutputDir, f"{album}.json")

            vocalStem = os.path.join(demucsOutputDir, f"vocals.mp3")

            if os.path.exists(vocalStem):
                destination = os.path.join(finalOutputDir, f"{songName}.mp3")
                shutil.move(vocalStem, destination)
                print(f"Moving {songName}.mp3 to {destination}")

                if os.path.exists(sourceJson):
                    try:
                        with self.manifestLock:
                            with open(sourceJson, "r") as f:
                                originalTracks = json.load(f)

                            currentTrack = next((track for track in originalTracks if track["title"] == songName), None)

                            if currentTrack:
                                processedTracks = []
                                if os.path.exists(destJson):
                                    with open(destJson, "r") as f:
                                        processedTracks = json.load(f)

                                if currentTrack not in processedTracks:
                                    processedTracks.append(currentTrack)

                                with open(destJson, "w") as f:
                                    json.dump(processedTracks, f, indent=4)

                            else:
                                print(f"Missing track in {sourceJson}: {songName}")

                    except Exception as e:
                            print(f"Failed to save {destJson}: error: {e}")

                try:
                    os.remove(filePath)
                    print(f"Removed {filePath}")
                except Exception as e:
                    print(f"Failed to remove {filePath}: {e}")

        except Exception as e:
            print(f"Missing vocals")

    def processAll(self, max=2):
        tracks = self.gatherTracks()
        print(f"Processing {len(tracks)} tracks")

        if not tracks:
            return

        with ThreadPoolExecutor(max_workers=max) as executor:
            futures = {executor.submit(self.processTrack, track): track[1] for track in tracks}

            for future in as_completed(futures):
                songName = futures[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"Failed to process {songName}: {exc}")



if __name__ == "__main__":

    preprocessor = Preprocessor()
    preprocessor.processAll(max=2)

    manager = DirectoryManager(musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music")
    manager.cleanDownloadDir()
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()
