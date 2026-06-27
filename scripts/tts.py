import csv
import os
import subprocess
import glob
import json
import shutil
import random
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

    '''
    def generateModel(self, artist,epochs=5000,  modelName=None):
        datasetDir = os.path.join(self.dir, "Dataset", artist)
        outputDir = os.path.join(self.dir, "models", artist)
        modelName = modelName or f"{artist}"

        os.makedirs(outputDir, exist_ok=True)
        print(f"Generating model for {artist}")

        trainCmd = [
            "python3", "-m", "piper_train",
            "--dataset-dir", datasetDir,
            "--output-dir", outputDir,
            "--epochs", str(epochs),
        ]

        try:
            subprocess.run(trainCmd, check=True)
            print(f"Training complete for {artist}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to train {artist}: {e}")
            return False

        print("Looking for checkpoints")
        checkpoints = glob.glob(os.path.join(outputDir, "*.ckpt"))
        if not checkpoints:
            print(f"No checkpoints found for {artist}")
            return False

        latestCheckpoint = max(checkpoints, key=os.path.getctime)
        print(f"Using checkpoint: {latestCheckpoint}")

        print(f"Exporting model for {artist} to ONNX")

        exportCmd = [
            "python3", "-m", "piper_trian.export_onnx",
            "--checkpoint", latestCheckpoint,
            "--output-dir", outputDir
        ]

        try:
            subprocess.run(exportCmd, check=True)
            print(f"Exported ONNX model for {artist}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to export ONNX for {artist}: {e}")
            return False
    '''

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


if __name__ == "__main__":
    generator = ModelGenerator()
    artists = ["Weezer", "Red Hot Chili Peppers", "Avril Lavigne", "Paramore", "The Beatles", "The Cardigans"]

    #for artist in artists:
        #generator.generateDataset(artist)

    for artist in artists:
        generator.pruneDataset(artist)







