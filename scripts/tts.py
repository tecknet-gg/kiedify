import os
import subprocess
import glob

class ModelGenerator:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.wavDir = os.path.join(self.dir, "WAV")
        os.makedirs(self.wavDir, exist_ok=True)

        self.tmpDir = os.path.join(self.wavDir, "tmp")
        os.makedirs(self.tmpDir, exist_ok=True)

    def cleanText(self, text):
        return text

    def convertToWAV(self, audioPath, outputPath=self.tmpDir, sampleRate=44100):
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
            "-i", inputAudio,
            "-ac", "1",
            "-ar", "22050",
            "-c:a", "pcm_s16le",
            outputWavPath
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
        datasetOutput = os.path.join(self.dir, "Dataset", artist, "wavs")
        os.makedirs(datasetOutput, exist_ok=True)

        manifestPath = os.path.join(inputDir, f"{artist}.json")
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
                    phrasetext = self.cleanText(phraseText)

                    sliceName = f"slice_{sliceCounter:06d}.wav"
                    slicePath = os.path.join(datasetOutput, sliceName)

                    success = self.sliceWAV(audioPath, groupStart, groupEnd, slicePath)
                    if success:
                        print(f"Sliced {title} into {sliceName}")
                        metadata_entries.append(f"slice_{slice_counter:06d}|{phrase_text}")
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







        