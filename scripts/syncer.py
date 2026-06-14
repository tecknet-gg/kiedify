import json
import os
import torch
import whisperx
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from scipy import butter, filtfilt


class Syncer:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music", modelName="wav2vec2-large-xlsr-53" , device = "cpu", computeType = "int16"):

        self.musicDir = musicDir
        self.device = device
        self.modelName = modelName
        self.align, self.metadata = whisperx.load_align_model(language_code="en", device=self.device, model_name=self.modelName)

        self.lock = threading.Lock()
        print(f"Loaded mode on {self.device}")


    def syncAll(self):
        processedDir = os.path.join(self.musicDir, "Processed2")

        if not os.path.exists(processedDir):
            print("Directory missing")
            return

        tasks = []
        total = 0

        for artist in os.listdir(processedDir):
            artistPath = os.path.join(processedDir, artist)
            if not os.path.isdir(artistPath):
                continue

            oldManifest = os.path.join(artistPath, f"{artist}.json")
            if not os.path.exists(oldManifest):
                print(f"Manifest missing for {artist}")
                continue

            try:
                with open(oldManifest, "r") as f:
                    trackCount = len(json.load(f))
                    total += trackCount
            except Exception as e:
                print(f"Failed to load manifest for {artist}: {e}")
                continue

            tasks.append((artist, artistPath, oldManifest))

        if not tasks:
            print("No artists to sync")
            return

        self.total = total
        self.completed = 0

        print(f"Starting sync for {len(tasks)} artists")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(self.processArtist, artist, artistPath, oldManifest): artist for artist, artistPath, oldManifest in tasks
            }

        for future in as_completed(futures):
            artist = futures[future]
            try:
                future.result()
                print(f"Synced {artist}")
            except Exception as e:
                print(f"Failed to sync {artist}: {e}")

        print("Syncing finished")

    def processArtist(self, artistName, artistPath, oldManifest):
        try:
            with open(oldManifest, "r") as f:
                oldTracks = json.load(f)
        except Exception as e:
            print(f"Failed to load manifest for {artistName}: {e}")
            return

        newManifestPath = os.path.join(artistPath, f"{artistName}Synced.json")
        tmpPath = os.path.join(artistPath, f"{artistName}SyncedTmp.json")

        for track in oldTracks:
            title = track.get("title")

            lyrics = track.get("lyrics")
            if not lyrics or not track.get("lyricsPath"):
                print(f"Skipping {title}, no lyrics found")
                continue

                with self.lock:
                    self.completed += 1
                continue

            audio = track.get("lyricsPath")
            if not audio or not os.path.exists(audio):
                print(f"Skipping {title}, no audio found")
                with self.lock:
                    self.completed += 1
                continue

            print(f"Aliging lyrics for {title}")

            cleanedLyrics = [
                {
                "text": self.cleanLyrics(line["text"]),
                "start": line["start"],
                "end": line["end"]
                }
                for line in lyrics
                if "text" in line and "start" in line and "end" in line
            ]



            wordTimestamps = self.generateWordTimestamps(audio, cleanedLyrics)

            syncedData = {
                "title": title,
                "artist": artistName,
                "album": track.get("album"),
                "id": track.get("id"),
                "duration": track.get("duration"),
                "lyricsID": track.get("lyricsID"),
                "audioPath": audio,
                "words": wordTimestamps,
            }

            with self.lock:
                existing = []
                if os.path.exists(newManifestPath):
                    try:
                        with open(newManifestPath, "r") as f:
                            existing = json.load(f)
                    except Exception as e:
                        print(f"Failed to load synced manifest for {title}: {e}")

                existing = [record for record in existing if record.get("title") != title]
                existing.append(syncedData)

                try:
                    with open(tmpPath, "w") as f:
                        json.dump(existing, f, indent=4)
                    os.replace(tmpPath, newManifestPath)
                except Exception as e:
                    print(f"Failed to save synced manifest for {title}: {e}")

                self.completed += 1
                percentage = (self.completed/self.total) * 100
                print(f"[Progress: {self.completed}/{self.total} Tracks Complete] ({percentage:.1f}%) Saved: \"{title}\"")

    def generateWordTimestamps(self, audioPath, lyrics):
        words = []
        try:
            segments = self.chunkLyrics(lyrics)

            if not segments:
                print(f"No segments found in lyrics data: {audioPath}")
                return []

            audio = whisperx.load_audio(audioPath)
            audio = self.highPass(audio, 16000)
            audio = audio * 0.9 / max(abs(audio)) # compression


            alignedResults = whisperx.align(segments, self.align, self.metadata, audio, self.device)  # char alignments maybe?

            for segment in alignedResults.get("segments", []):

                if not segment.get("words"):
                    continue

                segment["words"].sort(key=lambda x: x.get("start", 0))

                for word in segment["words"]:
                    if word.get("start") is None or word.get("end") is None:
                        continue
                    wordText = word.get("word", "")
                    if not wordText:
                        continue
                    words.append({
                        "word": word["word"],
                        "start": round(float(word["start"]), 2),
                        "end": round(float(word["end"]), 2),
                    })

        except Exception as e:
            print(f"Failed to generate word timestamps: {e} for {audioPath}")
            return []

        print(f"{len(words)} words aligned")
        return words

    def cleanLyrics(self, text):
        return (
            text.lower()
            .replace("’", "'")
            .replace(",", "")
            .replace(".", "")
            .replace("!", "")
            .replace("?", "")
            .strip()
        )


    def chunkLyrics(self, lyrics, maxDuration=8.0):
        chunks = []
        currentChunk = []
        chunkStart = None

        for line in lyrics:
            if chunkStart is None:
                chunkStart = line["start"]

            currentChunk.append(line)
            chunkEnd = line["end"]

            if (chunkEnd-chunkStart)>=maxDuration:
                chunks.append({
                    "text": "".join(currentChunk),
                    "start": chunkStart,
                    "end": chunkEnd,
                })
                currentChunk = []
                chunkStart = None

        if currentChunk:
            chunks.append({
                "text": "".join(line["text"] for line in currentChunk),
                "start": chunkStart,
                "end": chunkEnd[-1]["end"],
            })

        return chunks



    def highPass(self, audio, sampleRate, cutoff=100):
        nyquist = sampleRate * 0.5 # nyquist frequency - upper boundary for aliasing
        normalisedCutoff = cutoff / nyquist

        a, b = butter(N=2, Wn=normalisedCutoff, btype='high', analog=False)
        filtered = filtfilt(a, b, audio)
        return filtered

if __name__ == "__main__":
    syncer = Syncer()
    syncer.syncAll()








