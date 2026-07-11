import os
import sys
import subprocess
import urllib.request
from dotenv import load_dotenv
import shutil

class RVCGenerator:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.rvcRoot = os.path.join(self.projectRoot, "rvc")

        self.modelsRoot = os.path.join(self.musicDir, "models")
        self.rvcModels = os.path.join(self.modelsRoot, "rvc")

        os.makedirs(self.rvcRoot, exist_ok=True)
        load_dotenv()

    def downloadBases(self):
        print(f"Downloading RVC v2 bases")

        rmvpeDir = os.path.join(self.rvcRoot, "assets", "rmvpe")
        os.makedirs(rmvpeDir, exist_ok=True)



        models = {
            os.path.join(self.rvcModels, "hubert.pt"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
            os.path.join(self.rvcModels, "f0D40k.pth"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0D40k.pth",
            os.path.join(self.rvcModels, "f0G40k.pth"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0G40k.pth",
            os.path.join(rmvpeDir, "rmvpe.pt"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt"
        }
        for path, modelUrl in models.items():
            modelName = os.path.basename(path)
            if not os.path.exists(path):
                print(f"Downloading {modelName} from {modelUrl}")
                try:
                    urllib.request.urlretrieve(modelUrl, path)
                    print(f"Downloaded {modelName}")
                except Exception as e:
                    print(f"Failed to download {modelName}: {e}")
            else:
                print(f"Asset {modelName} exists :]")


    def runCommand(self, command):
        result = subprocess.run(command, cwd=self.rvcRoot)
        if result.returncode != 0:
            print(f"Failed to run command: {command}")
            raise RuntimeError(f"Failed to run command: {command}")

    def trainArtist(self, artist, epochs=200, batchSize=8):
        datasetDir = os.path.join(self.musicDir, "Dataset", artist, "wavs")
        expName = artist.replace(" ", "_")

        if not os.path.exists(datasetDir) or not os.listdir(datasetDir):
            print(f"Dataset {artist} doesn't exist or is empty.")
            return False

        logDir = os.path.join(self.rvcRoot, "logs", expName)
        os.makedirs(logDir, exist_ok=True)

        print(f"Training {artist}'s RVC model.")

        preprocess = [
            "python", "infer/modules/train/preprocess.py",
            datasetDir,
            "40000",
            "4",
            f"logs/{expName}",
            "False",
            "0.37" #overlap ratio
        ]


        self.runCommand(preprocess)

        featureExtraction1 = [
            "python", "infer/modules/train/extract/extract_f0_print.py",
            f"logs/{expName}",
            "4",
            "rmvpe"
        ]

        self.runCommand(featureExtraction1)

        featureExtraction2 = [
            "python", "infer/modules/train/extract/extract_feature_print.py",
            "mps", #cpu if not supported
            "1",
            "0",
            "0",
            f"logs/{expName}"
        ]

        self.runCommand(featureExtraction2)

        train = [
            "python", "infer/modules/train/train.py",
            "-e", expName,
            "-sr", "40k",
            "-f0", "1",
            "-bs", str(batchSize),
            "-te", str(epochs),
            "-se", "10", #save checkpoints
            "-pg", os.path.join(self.rvcModels, "f0G40k.pth"),
            "-pd", os.path.join(self.rvcModels, "f0D40k.pth"),
            "-l", "1",
            "-c", "0",
            "-sw", "1",
            "-v", "v2"
        ]

        self.runCommand(train)
        print(f"Finished training {artist}'s RVC model.")
        return True


    def exportModel(self, artist):
        expName = artist.replace(" ", "_")
        rvcLogDir = os.path.join(self.rvcRoot, "logs", expName)
        rvcWeightsFile = os.path.join(self.rvcRoot, "assets", "weights", f"{expName}.pth")

        destination = os.path.join(self.modelsRoot, artist , expName)
        os.makedirs(destination, exist_ok=True)

        print(f"Exporting {artist}'s RVC model to {destination}")
        exported = False

        if os.path.exists(rvcWeightsFile):
            shutil.copy(rvcWeightsFile, os.path.join(destination, f"{expName}.pth"))
            print(f"Exported {artist}'s RVC model to {destination}")
            exported = True
        else:
            print(f"Global weights file for {artist}'s RVC model not found.")


        if os.path.exists(rvcLogDir):
            for file in os.listdir(rvcLogDir):
                if file.endswith(".index") and "added" in file:
                    shutil.copy(os.path.join(rvcLogDir, file), os.path.join(destination, file))
                    print(f"Exported {artist}'s index file {file} to {destination}")
                    exported = True

        if exported:
            print(f"Exported {artist}'s RVC model to {destination}")
        else:
            print(f"Failed to export {artist}'s RVC model to {destination}")

if __name__ == "__main__":
    rvc = RVCGenerator()
    artists = ["Weezer", "Red Hot Chili Peppers", "The Pretenders", "Fleetwood Mac"]
    rvc.downloadBases()
    rvc.trainArtist(artist=artists[0], epochs=200, batchSize=8)
    #rvc.exportModel(artists[0])
