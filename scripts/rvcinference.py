import os
import sys
import glob
import subprocess

class RVCInference:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.projectRoot = self.musicDir.rsplit("/", 1)[0]
        self.rvcRoot = os.path.join(self.musicDir, "rvc")
        self.modelsRoot = os.path.join(self.musicDir, "models")

        self.modelIndex = {}
        self.indexModels()

    def indexModels(self):
        print("Indexing models")

        if not os.path.exists(self.modelsRoot):
            print("No models directory exists, exiting")
            return

        pthFiles = glob.glob(os.path.join(self.modelsRoot,"**" , "*.pth"), recursive=True)
        for pth in pthFiles:
            name = os.path.basename(pth)


