import sys
import os
import glob
from piper import PiperVoice
import wave
import subprocess


class TTS:
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

        onnxPattern = os.path.join(self.modelsDir, "**", "*.onnx")
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
        artistKey = artist.lower()

        if modelPath is None:
            if artistKey not in self.index:
                print(f"No model found for {artistKey}")
                return False
            onnxPath = self.index[artistKey]["onnx"]
            jsonPath = self.index[artistKey]["json"]
        else:
            onnxPath = modelPath
            jsonPath = f"{modelPath}.json"

        stitchedDir = os.path.join(self.dir, "Stitched")
        os.makedirs(stitchedDir, exist_ok=True)

        wavPath = os.path.join(stitchedDir, f"{fileName}.wav")
        mp3Path = os.path.join(stitchedDir, f"{fileName}.mp3")

        print(f"Generating audio from {text} to {wavPath}")

        print(f"Loading piper voice from {onnxPath}")
        try:
            voice = PiperVoice.load(onnxPath, config_path=jsonPath)
            print(f"Successfully loaded {onnxPath}")
        except Exception as e:
            print(f"Failed to load {onnxPath}")

        print(f"Generating audio from {text} to {wavPath}")
        try:
            with wave.open(wavPath, "wb") as wav:
                voice.synthesize_wav(text, wav)
            print(f"Successfully generated {wavPath}")
        except Exception as e:
            print(f"Failed to synthesize {text} to {wavPath}")
            print(e)
            if os.path.exists(wavPath):
                os.remove(wavPath)

        final = self.convertToMP3(wavPath, mp3Path)

    def convertToMP3(self, inputWav, outputMP3, delete=True):
        print(f"Converting {inputWav} to {outputMP3}")

        ffmpegCmd = [
            "ffmpeg", "-y",
            "-i", inputWav,
            "-codec:a", "libmp3lame",
            "-q:a", "2",
            outputMP3,
        ]

        try:
            subprocess.run(ffmpegCmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Successfully converted {inputWav} to mp3")
            if delete and os.path.exists(inputWav):
                os.remove(inputWav)
                print(f"Cleaned up temporary file {inputWav}")
            return outputMP3
        except Exception as e:
            print(f"Failed to convert {inputWav} to mp3")
            print(e)
            return False

if __name__ == "__main__":
    inference = TTS()
    inference.indexModels()
    print(inference.index)
    inference.synthesise("hello guys how are we doing today", "Weezer")