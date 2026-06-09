import json
import os
import torch
import whisperx


class Syncer:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music", modelSize = "base", device = "cpu", computeType = "int16"):

        self.musicDir = musicDir

        self.modelSize = modelSize
        self.device = device
        self.computeType = computeType

        self.model = whisperx.load_model(self.modelSize, device=self.device, compute_type=self.computeType)
        print(f"Loaded model: {self.modelSize} on {self.device} with compute type: {self.computeType}")

    def syncAll(self):
        processedDir = os.path.join(self.musicDir, "Processed")

        if not os.path.exists(processedDir):
            print("Directory missing")
            return

        for artist in os.listdir(processedDir):
            artistPath = os.path.join(processedDir, artist)
            if not os.path.isdir(artistPath):
                continue

            oldManifest = os.path.join(artistPath, f"{artist}.json")
            if not os.path.exists(oldManifest):
                print(f"Manifest missing for {artist}")
                continue

            print(f"Syncing {artist}")
            self.processArtist(artist, artistPath, oldManifest)

        print("Syncing finished")



    def processArtist(self, artistName, artistPath, oldManifest):
        try:
            with open(oldManifest, "r") as f:
                oldTracks = json.load(f)
        except Exception as e:
            print(f"Failed to load manifest for {artistName}: {e}")
            return

        newManifest = []

        for track in oldTracks:
            title = track.get("title")
            audioPath = track.get("lyricsPath")
            if not audioPath or not os.path.exists(audioPath):
                print(f"Audio file missing for {title} by {artistName}")
                continue

            print("Generating word alignment")
            wordTimestamps = self.generateWordTimestamps(audioPath)

            syncedData = {
                "title": title,
                "artist": artistName,
                "album": track.get("album"),
                "id": track.get("id"),
                "duration": track.get("duration"),
                "lyricsID": track.get("lyricsID"),
                "audioPath": audioPath,
                "words": wordTimestamps,
            }
            newManifest.append(syncedData)

            newManifestPath = os.path.join(artistPath, f"{artistName}Synced.json")
            try:
                with open(newManifestPath, "w") as f:
                    json.dump(newManifest, f, indent=4)
                print(f"Synced manifest saved to {newManifestPath}")
            except Exception as e:
                print(f"Failed to save synced manifest for {artistName}: {e}")

    def generateWordTimestamps(self, audioPath):
        pass