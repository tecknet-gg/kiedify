import os
import json
import random
from pydub import AudioSegment

class RVCTrainer:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.rootDir = os.path.dirname(self.musicDir)


    def makeDataset(self, artist, targetDuration=60):
        targetDir = os.path.join(self.rootDir, "Applio", "assets", "datasets", artist)
        os.makedirs(targetDir, exist_ok=True)

        source = os.path.join(self.musicDir,"Processed" ,artist)
        if not os.path.exists(source):
            print(f"{source}")
            print(f"No source for {artist}")
            return False

        jsonFile = os.path.join(source, f"{artist}Synced.json")
        if not os.path.exists(jsonFile):
            print(f"No json file for {artist}")
            return False

        print(f"Found {jsonFile}")

        segments = []

        try:
            with open(jsonFile) as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load {jsonFile}")

        tracks = data if isinstance(data, list) else [data]

        for trackData in tracks:
            title = trackData.get("title")
            words = trackData.get("words", [])

            if not words:
                continue

            vocalMP3Path = os.path.join(self.musicDir, "Processed", artist, f"{title}.mp3")
            if not os.path.exists(vocalMP3Path):
                print(f"{vocalMP3Path} does not exist for {title} ")
                continue

            phrases = []
            currentPhrase = []
            maxGapSeconds = 1.5

            for wordInfo in words:
                wordStart = wordInfo["start"]
                wordEnd = wordInfo["end"]

                if not currentPhrase:
                    currentPhrase.append(wordInfo)
                else:
                    lastEnd = currentPhrase[-1]["end"]
                    if wordStart - lastEnd <= maxGapSeconds:
                        currentPhrase.append(wordInfo)
                    else:
                        phrases.append(currentPhrase)
                        currentPhrase = [wordInfo]

            if currentPhrase:
                phrases.append(currentPhrase)

            for phrase in phrases:
                phraseStartMs = int(phrase[0]["start"] * 1000)
                phraseEndMs = int(phrase[-1]["end"] * 1000)
                durationMs = phraseEndMs - phraseStartMs

                if durationMs >= 1500:
                    segments.append({
                        "audioPath": vocalMP3Path,
                        "startMs": phraseStartMs,
                        "endMs": phraseEndMs,
                        "durationMs": durationMs
                    })

            print(f"Found {len(segments)} segments for {title} ")

        if not segments:
            print("No valid segments compiled. Exiting")
            return False

        random.shuffle(segments)

        targetTotalMs = targetDuration * 60 * 1000
        currentTotalMs = 0
        chunkCounter = 0

        for segment in segments:
            if currentTotalMs >= targetTotalMs:
                break

            try:
                audio = AudioSegment.from_mp3(segment["audioPath"])
                start = max(0, segment["startMs"])
                end = min(len(audio), segment["endMs"])

                vocalSlice = audio[start:end]
                baseName = os.path.basename(segment["audioPath"])
                trackStem = os.path.splitext(baseName)[0]

                chunkName = f"{trackStem}_chunk_{chunkCounter:04d}.mp3"
                outputPath = os.path.join(targetDir, chunkName)

                vocalSlice.export(outputPath, format="mp3", bitrate="192k")

                currentTotalMs += (end - start)
                chunkCounter += 1

                if chunkCounter % 10 == 0 or currentTotalMs >= targetTotalMs:
                    progressMins = currentTotalMs / 1000 / 60
                    print(f"Exported: {progressMins} mins / {targetDuration} mins")

            except Exception as e:
                print(f"Failed to generate chunk {chunkCounter}: {e}")
                continue

        finalMins = currentTotalMs / 1000 / 60
        print(f"Created {chunkCounter} chunks ({finalMins:.2f} mins total)")
        return True


if __name__ == "__main__":
    trainer = RVCTrainer()
    trainer.makeDataset("Weezer")