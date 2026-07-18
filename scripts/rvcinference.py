import os
import asyncio
import edge_tts

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

        self.index = {}
        for artistFolder in os.listdir(self.modelsDir):
            artistPath = os.path.join(self.modelsDir, artistFolder)

            if not os.path.isdir(artistPath):
                continue

            modelKey = artistFolder.lower()

            pthFile = None
            indexFile = None

            for filename in os.listdir(artistPath):
                filePath = os.path.join(artistPath, filename)
                filename.lower()
                if filename.endswith(".pth"):
                    pthFile = filePath
                elif filename.endswith(".index"):
                    indexFile = filePath

            if pthFile or indexFile:
                self.index[modelKey] = {
                    "artistName": artistFolder,
                    "pth": pthFile,
                    "index": indexFile,
                }

            print(f"Indexed {modelKey}: {pthFile}")

        print(f"Indexed {len(self.index)} models")
        return True

    async def synthesise(self, gender):
        pass

if __name__ == "__main__":
    rvc = RVC()
    rvc.indexModels()
    print(rvc.index)