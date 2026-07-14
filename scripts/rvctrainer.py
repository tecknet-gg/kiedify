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

        os.makedirs(self.rvcModels, exist_ok=True)

        os.makedirs(self.rvcRoot, exist_ok=True)
        load_dotenv()

    def downloadBases(self):
        print(f"Downloading RVC v2 bases")

        rmvpeDir = os.path.join(self.rvcRoot, "assets", "rmvpe")
        hubertDir = os.path.join(self.rvcRoot, "assets", "hubert")

        os.makedirs(rmvpeDir, exist_ok=True)



        models = {
            os.path.join(self.rvcModels, "hubert.pt"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
            os.path.join(self.rvcModels, "f0D48k.pth"): "https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/pretrained_v2/f0D48k.pth",
            os.path.join(self.rvcModels, "f0G48k.pth"): "https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/pretrained_v2/f0G48k.pth",
            os.path.join(rmvpeDir, "rmvpe.pt"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt",

            os.path.join(hubertDir, "hubert_base.pt"): "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
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
        print(f"Running : {command}")

        result = subprocess.run(command, cwd=self.rvcRoot)

        if result.returncode != 0:
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
            sys.executable, "infer/modules/train/preprocess.py",
            datasetDir,
            "48000",
            "4",
            f"logs/{expName}",
            "False",
            "0.37" #overlap ratio
        ]


        self.runCommand(preprocess)

        featureExtraction1 = [
            sys.executable, "infer/modules/train/extract/extract_f0_print.py",
            f"logs/{expName}",
            "4",
            "rmvpe"
        ]

        self.runCommand(featureExtraction1)

        featureExtraction2 = [
            sys.executable, "infer/modules/train/extract_feature_print.py",
            "cpu", #cpu if not supported
            "1",
            "0",
            "0",
            f"logs/{expName}",
            "v2",
            "False"
        ]

        self.runCommand(featureExtraction2)


        sourceConfig = os.path.join(self.rvcRoot, "configs", "v2", "48k.json")
        destConfig = os.path.join(logDir, "config.json")

        if os.path.exists(sourceConfig):
            shutil.copy(sourceConfig, destConfig)
            print(f"Moved 48k config json to {destConfig}")
        else:
            raise FileNotFoundError(f"Failed to find {sourceConfig}")

        train = [
            sys.executable, "infer/modules/train/train.py",
            "-e", expName,
            "-sr", "48k",
            "-f0", "1",
            "-bs", str(batchSize),
            "-te", str(epochs),
            "-se", "10", #save checkpoints
            "-pg", os.path.join(self.rvcModels, "f0G48k.pth"),
            "-pd", os.path.join(self.rvcModels, "f0D48k.pth"),
            "-l", "1",
            "-c", "0",
            "-sw", "1",
            "-v", "v2"
        ]

        self.createFileList(expName)

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


    def createFileList(self, expName, version="v2", spkId=0):
        expDir = os.path.join(self.rvcRoot, "logs", expName)
        gtWavsDir = os.path.join(expDir, "0_gt_wavs")
        featureDir = os.path.join(expDir, "3_feature768")

        f0Dir = os.path.join(expDir, "2a_f0")
        f0nsfDir = os.path.join(expDir, "2b-f0nsf")

        names = (
                set(name.split(".")[0] for name in os.listdir(gtWavsDir))
                &
                set(name.split(".")[0] for name in os.listdir(featureDir))
                &
                set(name.split(".")[0] for name in os.listdir(f0Dir))
                &
                set(name.split(".")[0] for name in os.listdir(f0nsfDir))
        )

        filelist = []

        for name in names:
            filelist.append(
                f"{gtWavsDir}/{name}.wav|"
                f"{featureDir}/{name}.npy|"
                f"{f0Dir}/{name}.wav.npy|"
                f"{f0nsfDir}/{name}.wav.npy|"
                f"{spkId}"
            )

        filelistPath = os.path.join(expDir, "filelist.txt")

        with open(filelistPath, "w", encoding="utf-8") as f:
            f.write("\n".join(filelist))

        print(f"Created {len(filelist)} filelist.")

if __name__ == "__main__":
    rvc = RVCGenerator()
    artists = ["Weezer", "Red Hot Chili Peppers", "The Pretenders", "Fleetwood Mac"]
    rvc.downloadBases()

    #rvc.trainArtist(artists[0], epochs=200, batchSize=8)

    for i, artist in enumerate(artists):
        if i == 0:
            continue
        rvc.trainArtist(artist, epochs=200, batchSize=8)
        rvc.exportModel(artist)


