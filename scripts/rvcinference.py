import os
import sys

scriptDir = os.path.dirname(os.path.realpath(__file__))
projectRoot = os.path.abspath(os.path.join(scriptDir, ".."))

if projectRoot not in sys.path:
    sys.path.insert(0, projectRoot) #fix env runtime issue

import glob
import subprocess
from scipy.io import wavfile
from rvc.tools.onnx_inference_demo import f0_method
from rvc.modules.vc.modules import vc_single


class RVC:
    def __init__(self, dir="/Users/jeevan/Documents/Python/Music"):
        self.dir = dir
        self.modelsDir = os.path.join(self.dir, "models", "rvc")
        self.index = {}

        self.vc = None
        self.netG = None

    def indexModels(self):
        print("Indexing models")
        if not os.path.exists(self.modelsDir):
            print(f"Models directory does not exist: {self.modelsDir}")
            return

        pthPattern = os.path.join(self.modelsDir, "**", "*.pth")
        pthFiles = glob.glob(pthPattern, recursive=True)

        for pthPath in pthFiles:
            filename = os.path.basename(pthPath)

            if "f0D" in filename or "f0G" in filename or "hubert" in filename:
                continue

            artist = filename.split(".")[0].lower()
            if "-" in artist:
                artist = artist.split("-")[1].lower()

            parentDir = os.path.dirname(pthPath)
            indexPattern = os.path.join(parentDir, "*.index")
            indexFiles = glob.glob(indexPattern)
            indexPath = indexFiles[0] if indexFiles else ""

            self.index[artist] = {
                "pth": pthPath,
                "index": indexPath
            }
            print(f"Added {artist} to index: {pthPath}")

    def synthesise(self, artist, inputPath, outputPath="output.mp3", pitchChange=0):
        artistKey = artist.lower()

        if artistKey not in self.index:
            print(f"Artist {artist} not found in index: {self.index[artistKey]}")
            return False

        pthPath = self.index[artistKey]["pth"]
        indexPath = self.index[artistKey]["index"]

        tempWavOutput = os.path.join(self.dir, "temp.wav")

        print(f"Processing target voice")

        try:
            message, audioOut = vc_single(
                sid=0,
                input_audio_path=inputPath,
                f0_up_key=pitchChange,
                f0_file=None,
                f0_method=f0_method,
                file_index=indexPath,
                file_index2="",
                index_rate=0.75,
                filter_radius=3,
                resample_sr=0,
                rms_mix_rate=0.25,
                protect=0.33
            )

            targetSr, audioData = audioOut
            wavfile.write(tempWavOutput, targetSr, audioData)

            self.convertToMP3(tempWavOutput, outputPath, delete=True)
            return True
        except Exception as e:
            print(f"Failed to synthesize: {e}")
            return False

    def convertToMP3(self, inputWav, outputMP3, delete=True):
        print(f"Converting {inputWav} to {outputMP3}")

        ffmpegCmd = [
            "ffmpeg", "-y",
            "-i", inputWav,
            "-c:a", "libmp3lame",
            "-q:a", "2",
            outputMP3,
        ]

        try:
            subprocess.run(ffmpegCmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Successfully converted {inputWav} to {outputMP3}")
            if delete and os.path.exists(inputWav):
                os.remove(inputWav)
                print(f"Cleaned up {inputWav}")
            return outputMP3
        except Exception as e:
            print(f"Failed to convert {inputWav} to {outputMP3}: {e}")
            return False


