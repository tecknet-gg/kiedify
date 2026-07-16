import os
class RVC:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.rootDir = os.path.dirname(self.musicDir)
        self.modelsDir = os.path.join(self.musicDir, "models")

        self.index = {}

    def indexModels(self):
        if not os.path.exists(self.modelsDir):
            os.makedirs(self.modelsDir)
            print(f"Missing models dir: {self.modelsDir}")
            return False

    def synthesise(self):
        pass
