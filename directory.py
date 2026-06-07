import os
import json
import shutil
import time
import threading


class DirectoryManager:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = musicDir
        self.rawDir = os.path.join(musicDir,"Raw")
        self.targetDir = os.path.join(musicDir, "Isolated")
        pass

    def cleanDownloadDir(self):
        for artist in os.listdir(self.rawDir):
            artistPath = os.path.join(self.rawDir, artist) #creating the ~/Raw/Weezer path
            if not os.path.isdir(artistPath): #skip if doesn't exist
                continue

            for album in os.listdir(artistPath):
                albumPath = os.path.join(artistPath, album)
                if not os.path.isdir(albumPath):
                    continue #same as before at the album level

                for root, dirs, files in os.walk(albumPath, topdown=False):
                    if root == albumPath: #skip is the root of every file is the same as the album's path
                        continue

                    for file in files:
                        curentPath = ""
                        targetPath = ""

                        if file.endswith(".mp3"):
                            currentPath = os.path.join(root, file)
                            targetPath = os.path.join(albumPath, file) #targets the album root

                        try:
                            shutil.move(currentPath, targetPath)
                        except shutil.Error as error:
                            print(f"Error moving {currentPath} to {targetPath}: {error}")

                        try:
                            if not os.listdir(root):
                                os.rmdir(root)
                        except OSError as error:
                            print(f"Error deleting empty directory: {error}")

    def cleanIsolatedDir(self):
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

    def flattenProcessedDir(self):
        processedRoot = os.path.join(self.dir, "Processed")
        if not os.path.exists(processedRoot):
            print("Directory missing")
            return

        for artist in os.listdir(processedRoot):
            artistPath = os.path.join(processedRoot, artist)
            if not os.path.isdir(artistPath):
                continue

            artistManifestPath = os.path.join(artistPath, f"{artist}.json")
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

    def nukeRaw(self, target):
        if os.path.exists(target):
            shutil.rmtree(target)
            os.makedirs(target)
        print("Raw directory cleaned.")
