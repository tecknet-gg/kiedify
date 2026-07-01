import os
import sys
import subprocess
import urllib.request


class RVCGenerator:
    def __init__(self, musicDir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = musicDir
        self.modelsRoot = os.path.join(self.musicDir, "models")
        self.rvc = os.path.join(self.modelsRoot, "rvc")
        os.makedirs(self.rvc, exist_ok=True)

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


if __name__ == "__main__":
    rvc = RVCGenerator()
    rvc.downloadBases()