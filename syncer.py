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
            self.processArtist(artist)

        print("Syncing finished")







    def generateSync(self, lyrics, audio):
        pass

