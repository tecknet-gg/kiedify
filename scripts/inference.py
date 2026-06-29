import sys
import os
import glob


class Inference:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.modelsDir = os.path.join(self.dir, "models")
        self.index = {}

    def indexModels(self):
        self.index.clear()

        print("Indexing models")

        if not os.path.exists(self.modelsDir):
            print(f"Directory {self.modelsDir} doesn't exist")
            return

        onnxPattern = os.path.join(self.modelsDir, "*.onnx")
        onnxFiles = glob.glob(onnxPattern, recursive=True)

        for onnxPath in onnxFiles:
            filename = os.path.basename(onnxPath)

            parts = filename.split("-")
            if len(parts)>=3:
                artist = parts[1].lower()
                json = f"{onnxPath}.json"

                if os.path.exists(json):
                    self.index[artist] = {
                        "onnx": onnxPath,
                        "json": json,
                    }
                    print(f"Added artist {artist} to index")

        return self.index




    def synthesise(self, text, artist, fileName="output", modelPath=None):
        if modelPath is None:
            self.index[artist][1]

        outputWav = f"{artist}.wav"
        outputPath = os.join(self.dir, Stitched, outputWav)

        with wave.open(outputPath, "wb") as output:
            self.voice.synthesize(text, output)

        #convert to mp3

if __name__ == "__main__":
    inference = Inference()
    inference.indexModels()
    print(inference.index)