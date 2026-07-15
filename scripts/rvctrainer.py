import os
import json
import random
from pathlib import Path
from pydub import AudioSegment

class RVCTrainer:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.rootDir = self.musicDir.rsplit("/", 1)[0]


    def makeDataset(self, artist):
        targetDir = os.path.join(self.rootDir, "Applio", "assets", "datasets", artist)
        os.makedirs(targetDir, exist_ok=True)

        source = os.path.join(self.musicDir, artist)
        if not os.path.exists(source):
            return False

        jsonFile = os.path.join(source, f"{artist}Synced.json")
        if not os.path.exists(jsonFile):
            return False



if __name__ == "__main__":
    pass