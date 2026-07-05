import os
import sys
import subprocess
import urllib.request
from dotenv import load_dotenv

from rvc.modules.train.preprocess import preprocess_dataset
from rvc.modules.train.extract import extract_features
from rvc.modules.train.train import train_module


class RVCGenerator:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.modelsRoot = os.path.join(self.musicDir, "models")
        self.rvc = os.path.join(self.modelsRoot, "rvc")
        os.makedirs(self.rvc, exist_ok=True)

        load_dotenv()


    def downloadBases(self):
        print(f"Downloading RVC v2 bases")
        models = {
            "hubert.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt",
            "f0D40k.pth": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0D40k.pth",
            "f0G40k.pth": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0G40k.pth",
        }
        for modelName, modelUrl in models.items():
            localPath = os.path.join(self.rvc, modelName)
            if not os.path.exists(localPath):
                print(f"Downloading {modelName} from {modelUrl}")
                try:
                    urllib.request.urlretrieve(modelUrl, localPath)
                    print(f"Downloaded {modelName}")
                except Exception as e:
                    print(f"Failed to download {modelName}")
            else:
                print(f"Asset {modelName} exists :]")

    def trainArtist(self, artist, epochs=200, batchSize=8):
        datasetDir = os.path.join(self.musicDir, "Dataset", artist, "wavs")
        exportDir = os.path.join(self.musicDir, "Dataset", artist, "logs")
        os.makedirs(exportDir, exist_ok=True)

        if not os.path.exists(datasetDir) or not os.listdir(datasetDir):
            print(f"Dataset {artist} doesn't exist or is empty.")
            return False

        print(f"Preprocessing {artist} dataset.")
        preprocess_dataset(
            input_root=datasetDir,
            sr=40000,
            num_processes=4,
            exp_dir=exportDir
        )

        print(f"Extracting {artist} dataset.")
        extract_features(
            exp_dir=exportDir,
            n_p=4,
            f0method="rmvpe",
            device="mps"
        )

        print(f"Training {artist} model.")
        train_model(
            exp_dir=exportDir,
            if_f0=True,
            spk_id=0,
            version="v2",
            total_epoch=epochs,
            batch_size=batchSize,
            save_epoch_only=True
        )

        print(f"Finished training {artist} model. Weights are saved to {exportDir}")
        return True


    def exportModels(self, artist):
        pass



if __name__ == "__main__":
    #run script from terminal after switching to .venvRVC

    rvc = RVCGenerator()
    rvc.downloadBases()