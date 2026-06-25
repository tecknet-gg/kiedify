import os
import subprocess
import glob
import json

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


    def generateModel(self, artist, epochs=50, modelName=None, rvcRoot=None):
        if not modelName:
            modelName = f"{artist}"
        if not rvcRoot:
            dir = os.path.dirname(self.dir)
            rvcRoot = os.path.join(dir, "Applio")

        datasetFolder = os.path.join(self.dir, "Dataset", artist)
        expDir = os.path.join(rvcRoot, "logs", modelName)
        os.makedirs(expDir, exist_ok=True)

        print(f"Starting RVC training for {artist} with {epochs} epochs")

        print(f"Running preprocessing")

        preprocessCmd = [
            "python", os.path.join(rvcRoot, "rvc/train/preprocess/preprocess.py"), #/Users/jeevan/Documents/Python/MusicTTS/Applio/rvc/train/preprocess/preprocess.py
            datasetFolder,
            "40000", #sample rate
            "6", #cpu threads
            expDir,
            "False" #clean audio gain flag
        ]

        try:
            subprocess.run(preprocessCmd, check=True, cwd=rvcRoot)
            print(f"Preprocessing complete for {artist}")
        except subprocess.CalledProcessError as e:
            print(f"Preprocessing failed for {artist}: {e}")
            return False

        print(f"Running pitch extraction")
        extractionCmd = [
            "python", os.path.join(rvcRoot, "rvc/train/extract/extract.py"),
            expDir,
            "6",
            "rmvpe" #retina multi variable pitch extraction
        ]
        try:
            subprocess.run(extractionCmd, check=True, cwd=rvcRoot)
            print(f"Extraction complete for {artist}")
        except subprocess.CalledProcessError as e:
            print(f"Extraction failed for {artist}: {e}")
            return False

        print(f"Training model")

        trainCmd = [
            "python", os.path.join(rvcRoot, "rvc/train/train.py"),
            "-e", modelName,
            "-sr", "40k",
            "-f0", "1",
            "-ep,", str(epochs),
            "-b", "16", #batch size
            "-g", "0",
            "-p", "True", #save weights
            "-v", "v2" #literally just v2
        ]

        try:
            subprocess.run(trainCmd, check=True, cwd=rvcRoot)
            print(f"Training complete for {artist}")
        except subprocess.CalledProcessError as e:
            print(f"Training failed for {artist}: {e}")
            return False



if __name__ == "__main__":
    generator = ModelGenerator()
    #artists = ["Weezer", "Red Hot Chili Peppers", "Avril Lavigne", "Paramore", "The Beatles", "The Cardigans"]
    #for artist in artists:
        #generator.generateDataset(artist)

    generator.generateModel("Weezer", epochs=10, rvcRoot="/Users/jeevan/Documents/Python/MusicTTS/Applio")





        