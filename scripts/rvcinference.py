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

            if any(x in name for x in ["f0D", "f0G", "hubert"]):
                continue

            artist = name.split(".")[0].lower()

            folder = os.path.dirname(pth)
            indexFiles = glob.glob(os.path.join(folder, "*index"))

            self.modelIndex[artist] = {
                "pth": pth,
                "index": indexFiles[0] if indexFiles else ""
            }

        print("Indexed models")
        print(f"{self.modelIndex}")

    def synthesise(self, text, artist, inputWav, outputWav, pitch=0, filename=None):
        artist = artist.lower()

        if artist not in self.modelIndex:
            print("No model found, exiting")
            return False

        model = self.modelIndex[artist]["pth"]
        index = self.modelIndex[artist]["index"]

        print(f"Synthesizing {text} for {artist}")

        cmd = [
            sys.executable,
            "--input_path", model,
            "--output_path", outputWav,
            "--model_path", model,
            "--index_path", index,
            "--pitch", str(pitch),
            "--f0_method", "rmvpe",
            "-index_rate", "0.75",
            "--device", "cpu"
        ]

        try:
            subprocess.run(cmd)
            print(f"Successfully generated WAV file for {text}")
            #do mp3 conversion
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error generating WAV file for {text}: {e}")
            return False




