import csv
import os
import subprocess
import glob
import json
import shutil
import random
import urllib
import wave

class ModelGenerator:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.wavDir = os.path.join(self.dir, "WAV")
        os.makedirs(self.wavDir, exist_ok=True)

        self.tmpDir = os.path.join(self.wavDir, "tmp")
        os.makedirs(self.tmpDir, exist_ok=True)

    def cleanText(self, text):
        return text

    def convertToWAV(self, audioPath, outputPath, sampleRate=44100):
        print(f"Converting {audioPath} to WAV")
        cmd = [
            "ffmpeg", "-y", "-i", audioPath, "-ac", "1", "-ar", str(sampleRate), "-f", "wav", outputPath
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Converted {audioPath} to WAV")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to convert {audioPath}: {e}")
            return False

    def sliceWAV(self, audioPath, start, end, outputPath):
        duration = end-start

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.4f}",
            "-t", f"{duration:.4f}",
            "-i", audioPath,
            "-ac", "1",
            "-ar", "22050",
            "-c:a", "pcm_s16le",
            outputPath
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Sliced {audioPath} into {outputPath}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to slice {audioPath}: {e}")
            return False

    def generateDataset(self, artist, segmentLength=10.0):
        inputDir = os.path.join(self.dir, "Processed", artist)
        datasetOutput = os.path.join(self.dir, "Dataset", artist)
        os.makedirs(datasetOutput, exist_ok=True)

        manifestPath = os.path.join(inputDir, f"{artist}Synced.json")
        metadataPath = os.path.join(datasetOutput, f"metadata.csv")

        datasetOutput = os.path.join(datasetOutput, f"wavs")
        os.makedirs(datasetOutput, exist_ok=True)

        if not os.path.exists(manifestPath):
            print(f"Manifest missing for {artist}")
            return False

        with open(manifestPath, "r") as file:
            tracks = json.load(file)

        print(f"Generating piper dataset for {artist} with {len(tracks)} tracks")
        metadataEntries = []
        sliceCounter = 0

        for track in tracks:
            title = track.get("title")
            words = track.get("words", [])
            audioPath = os.path.join(inputDir, f"{title}.mp3")

            if not os.path.exists(audioPath):
                print(f"Audio file missing for {title}")
                continue

            if not words:
                print(f"Missing lyrics for {title}")
                continue

            print(f"Slicing {title} into {segmentLength} second segments")

            currentGroup = []
            groupStart = None

            for i, word in enumerate(words):
                if groupStart is None:
                    groupStart = word["start"]

                currentGroup.append(word)
                currentDuration = word["end"] - groupStart
                isLastWord = False

                if i == len(words)-1:
                    isLastWord = True

                nextWordExceeds = False
                if not isLastWord:
                    nextWord = words[i+1]
                    if "end" in nextWord:
                        if (float(nextWord["end"]) - groupStart) > segmentLength:
                            nextWordExceeds = True

                if isLastWord or nextWordExceeds:
                    groupEnd = float(currentGroup[-1]["end"])

                    phraseText = " ".join([word["word"] for word in currentGroup])
                    phraseText = self.cleanText(phraseText)

                    sliceName = f"slice_{sliceCounter:06d}.wav"
                    slicePath = os.path.join(datasetOutput, sliceName)

                    success = self.sliceWAV(audioPath, groupStart, groupEnd, slicePath)
                    if success:
                        print(f"Sliced {title} into {sliceName}")
                        metadataEntries.append(f"slice_{sliceCounter:06d}|{phraseText}")
                        sliceCounter += 1

                    currentGroup = []
                    groupStart = None

        if metadataEntries:
            with open(metadataPath, "w", encoding="utf-8") as file:
                for entry in metadataEntries:
                    file.write(entry + "\n")
                print(f"Wrote metadata for {artist} to {metadataPath}")
                return True
        else:
            print(f"No valid segments found for {artist}")
            return False

    def pruneDataset(self, artist, target=5): #total in hours
        metadataPath = os.path.join(self.dir, "Dataset", artist, "metadata.csv")
        wavDir = os.path.join(self.dir, "Dataset", artist, "wavs")

        if not os.path.exists(metadataPath):
            print(f"Metadata missing for {artist}")
            return False

        with open(metadataPath, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="|")
            rows = list(reader)

        random.shuffle(rows)

        selectedRows = []
        totalDuration = 0
        targetSeconds = target * 3600

        for row in rows:
            if totalDuration >= targetSeconds:
                break

            fileId = row[0]

            if not fileId.endswith(".wav"):
                wavPath = os.path.join(wavDir, f"{fileId}.wav")
            else:
                wavPath = os.path.join(wavDir, fileId)

            if os.path.exists(wavPath):
                try:
                    with wave.open(wavPath, "rb") as wavFile:
                        frames = wavFile.getnframes()
                        rate = wavFile.getframerate()
                        duration = frames / float(rate)

                    totalDuration += duration
                    selectedRows.append(row)

                except Exception as e:
                    print(f"Failed to read {wavPath}: {e}")

        with open(metadataPath, "w", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="|")
            writer.writerows(selectedRows)

        actualHours = totalDuration / 3600
        print(f"Pruned {artist} dataset to {len(selectedRows)} rows ({actualHours:.2f} hours)")
        return True

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
            localCpkt = os.path.join(assets["dir"], "base.cpkt")

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
            "python3", "-m", "piper_train.preprocess",
            "--language", "en-us",
            "--input-dir", artistPath,
            "--output-dir", artistPath,
            "--dataset-format", "ljspeech",
            "--single-speaker",
            "--sample-rate", "22050"
        ]

        try:
            subprocess.run(preprocessCmd, check=True)
            print("Successfully preprocessed {artist}")
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
            "python3", "-m", "piper_train",
            "--dataset-dir", artistPath,
            "--accelerator", "gpu",
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

        import torch
        import pathlib
        import sys

        try:
            torch.serialization.add_safe_globals([pathlib.PosixPath])
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
    generator = ModelGenerator()
    artists = ["Weezer", "Red Hot Chili Peppers", "Avril Lavigne", "Paramore", "The Beatles", "The Cardigans"]

    #for artist in artists:
        #generator.generateDataset(artist)

    #for artist in artists:
        #generator.pruneDataset(artist)

    #generator.downloadBases(artists[0])
    #generator.generateModel(artists[0],gender="male", resume=True)

    generator.exportModel(artists[0])






