import csv
import os
import subprocess
import glob
import json
import shutil
import random
import urllib
import wave
import torch
import pathlib
import sys

class TTSGenerator:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir

    def downloadBases(self):
        root = os.path.join(self.dir, "models")

        targets = {
            "male": {
                "dir": os.path.join(root, "male"),
                "config": "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_male/medium/config.json",
                "ckpt": "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_male/medium/epoch%3D2785-step%3D2128064.ckpt"
            },
            "female": {
                "dir": os.path.join(root, "female"),
                "config": "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_female/medium/config.json",
                "ckpt": "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_female/medium/epoch%3D2868-step%3D1575188.ckpt"
            }
        }

        for gender, assets in targets.items():
            os.makedirs(assets["dir"], exist_ok=True)
            localConfig = os.path.join(assets["dir"], "config.json")
            localCpkt = os.path.join(assets["dir"], "base.ckpt")

            if not os.path.exists(localConfig):
                print(f"Downloading {gender} to {localConfig}")
                try:
                    urllib.request.urlretrieve(assets["config"], localConfig)
                    print(f"Downloaded {gender} to {localConfig}")
                except Exception as e:
                    print(f"Failed to download {gender}: {e}")

            if not os.path.exists(localCpkt):
                print(f"Downloading {gender} to {localCpkt}")
                try:
                    urllib.request.urlretrieve(assets["ckpt"], localCpkt)
                    print(f"Downloaded {gender} to {localCpkt}")
                except Exception as e:
                    print(f"Failed to download {gender}: {e}")
        print("Done")

    def generateJsonl(self, artist):

        artistPath = os.path.join(self.dir, "Dataset", artist)
        os.makedirs(artistPath, exist_ok=True)

        datasetJsonlPath = os.path.join(artistPath, "dataset.jsonl")

        print(f"Generating {artist} dataset.jsonl")
        preprocessCmd = [
            sys.executable, "-m", "piper_train.preprocess",
            "--language", "en-us",
            "--input-dir", artistPath,
            "--output-dir", artistPath,
            "--dataset-format", "ljspeech",
            "--single-speaker",
            "--sample-rate", "22050"
        ]

        try:
            subprocess.run(preprocessCmd, check=True)
            print(f"Successfully preprocessed {artist}")
            return True
        except Exception as e:
            print(f"Failed to preprocess: {e}")
            return False

    def generateModel(self, artist, gender,  epochs=10000, batchSize=32, resume=True, explicitCheckpoint=False):
        artistPath = os.path.join(self.dir, "Dataset", artist)
        configOutputPath = os.path.join(artistPath, "config.json")

        if gender not in ["male", "female"]:
            return

        datasetJsonlPath = os.path.join(artistPath, "dataset.jsonl")
        if not os.path.exists(datasetJsonlPath):
            self.generateJsonl(artist)

        baseCheckpoint = os.path.join(self.dir, "models", f"{gender}", "base.cpkt")


        if not os.path.exists(configOutputPath):
            modelPath = os.path.join(self.dir, "models")
            jsonFiles = glob.glob(os.path.join(modelPath, gender ,"*.json"))

            if jsonFiles:
                baseJsonPath = jsonFiles[0]
                shutil.copyfile(baseJsonPath, configOutputPath)
                print("Created config.json")
            else:
                print("No config.json found")
                return False

        cmd = [
            sys.executable, "-m", "piper_train",
            "--dataset-dir", artistPath,
            "--accelerator", "mps",
            "--devices", "1",
            "--batch-size", str(batchSize),
            "--validation-split", "0.05",
            "--num-test-examples", "0",
            "--max_epochs", str(epochs),
            "--checkpoint-epochs", str(1),
            "--precision", "32"
        ]

        checkpoint = None

        if explicitCheckpoint and os.path.exists(explicitCheckpoint):
            checkpoint = explicitCheckpoint

        elif resume:
            print(f"Finding checkpoint for {artist}")
            searchPattern = os.path.join(artistPath, "lightning_logs", "**", "checkpoints", "*.ckpt")
            foundCheckpoints = glob.glob(searchPattern, recursive=True)

            if foundCheckpoints:
                checkpoint = max(foundCheckpoints, key=os.path.getmtime)
                print(f"Found checkpoint: {checkpoint}")
            else:
                print(f"No checkpoint found for {artist}")

        if not checkpoint and os.path.exists(baseCheckpoint):
            checkpoint = baseCheckpoint
            print(f"Starting from base checkpoint {baseCheckpoint}")
        elif not checkpoint:
            print(f"Missing basess, run downloadBases first.")
            return False

        if checkpoint:
            cmd.extend(["--resume_from_checkpoint", checkpoint]) #add checkpoint to resume from

        print(f"Beginning training for {artist}")

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Training complete for {artist}")
            return True
        except Exception as e:
            print(f"Failed to train {artist}: {e}")
            return False

    def exportModel(self, artist):
        artistDataset = os.path.join(self.dir, "Dataset", artist)
        artistModelPath = os.path.join(self.dir, "models", artist)

        chkptPattern = os.path.join(artistDataset, "lightning_logs", "**", "checkpoints", "*.ckpt")
        checkpoints = glob.glob(chkptPattern, recursive=True)

        if not checkpoints:
            print(f"No checkpoints found for {artist}")
            return False

        largest = max(checkpoints, key=os.path.getsize) #choose largest checkpoint

        os.makedirs(artistModelPath, exist_ok=True)
        onnxName = f"en_US-{artist.lower()}-medium.onnx"

        onnxPath = os.path.join(artistModelPath, onnxName)
        onnxJsonPath = f"{onnxPath}.json"

        sourceConfig = os.path.join(artistDataset, "config.json")

        print(f"Exporting {artist} model to {onnxPath}")

        try:
            originalTorch = torch.load()
            @functools.wraps(originalTorch)
            def patchedTorch(*args, **kwargs):
                kwargs["weights_only"] = False
                return originalTorch(*args, **kwargs)
            
            original = torch.onnx.export            
            def patch(*args, **kwargs):
                kwargs["dynamo"] = False
                return original(*args, **kwargs)
            torch.onnx.export = patch
            import piper_train.export_onnx as exp

            originalArgv = sys.argv.copy()
            sys.argv = ["export_onnx", largest, onnxPath]

            try:
                exp.main()
            except Exception as e:
                print(f"Failed to export {artist}: {e}")

            sys.argv = originalArgv
            torch.load = originalTorch
            print(f"Exported {artist} to {onnxPath}")

            if os.path.exists(sourceConfig):
                shutil.copyfile(sourceConfig, onnxJsonPath)
                print(f"Exported {artist} to {onnxJsonPath}")
            else:
                print(f"Missing config.json")

            return True
        except Exception as e:
            print(f"Failed to export {artist}: {e}")
            return False


if __name__ == "__main__":
    generator = TTSGenerator()
    artists = ["Weezer", "Red Hot Chili Peppers", "Avril Lavigne", "Paramore", "The Beatles", "The Cardigans"]

    #for artist in artists:
        #generator.generateDataset(artist)

    #for artist in artists:
        #generator.pruneDataset(artist)

    #generator.downloadBases(artists[0])
    #generator.generateModel(artists[0],gender="male", resume=True)
    generator.exportModel(artists[0])






