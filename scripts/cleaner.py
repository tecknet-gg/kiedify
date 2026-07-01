import os
from difflib import SequenceMatcher

import whisperx
import re
import torch
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading



class Cleaner:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.device = "cpu" #you should probably change this to cuda if your setup supports that
        computeType = "float32" #float16 if cuda
        self.model = whisperx.load_model("large-v3", device=self.device, compute_type=computeType)
        self.lock = threading.Lock()

        self.alignModelCache = {}
        self.alignModelLock = threading.Lock()


    def getAlignModel(self, languageCode):
        with self.alignModelLock:
            if languageCode not in self.alignModelCache:
                modelA, metadata = whisperx.load_align_model(language_code=languageCode, device=self.device)
                self.alignModelCache[languageCode] = (modelA, metadata)
            return self.alignModelCache[languageCode]

    def cleanText(self, text):
        text = text.lower().strip()
        text = re.sub(r'[()\[\]{}.,!?;\"]', '', text)
        return text.replace('-', ' ')

    def saveProgress(self, manifestPath, tempOutputPath, updatedTrack):
        with self.lock:
            try:
                if os.path.exists(manifestPath):
                    with open(manifestPath, "r") as f:
                        currentTracks = json.load(f)
                else:
                    currentTracks = []

                for i, track in enumerate(currentTracks):
                    if track.get("title") == updatedTrack.get("title"):
                        currentTracks[i] = updatedTrack
                        break
                else:
                    currentTracks.append(updatedTrack)

                with open(tempOutputPath, "w") as f:
                    json.dump(currentTracks, f, indent=4)
                os.replace(tempOutputPath, manifestPath)
            except Exception as e:
                print(f"Failed to save progress: {e}")
                if os.path.exists(tempOutputPath):
                    os.remove(tempOutputPath)

    def cleanAristCorpus(self, artist, tolerance=0.75):

        processedDir = os.path.join(self.musicDir, "Processed", artist)
        manifestPath = os.path.join(processedDir, f"{artist}Synced.json")
        tempOutputPath = os.path.join(processedDir, f"{artist}Synced.tmp")

        if not os.path.exists(manifestPath):
            print(f"Manifest missing for {artist}")
            return False

        with open(manifestPath, "r") as f:
            tracks = json.load(f)

        cleanedTracks = []
        skipped = 0
        print(f"Cleaning {artist}'s corpus")

        for track in tracks:
            title = track.get("title")
            officialWords = track.get("words", [])
            audioPath = os.path.join(processedDir, f"{title}.mp3")

            if not audioPath or not os.path.exists(audioPath):
                print(f"Audio file missing for {track['title']}")
                continue

            if self.isAlreadyChecked(track):
                print(f"Already checked {track['title']}, skipping")
                cleanedTracks.append(track)
                skipped += 1
                continue

            print(f"Cleaning {track['title']}")



            try:
                audio = whisperx.load_audio(audioPath)
                result = self.model.transcribe(audio, batch_size=16, language="en")
                modelA, metadata = self.getAlignModel(languageCode=result["language"])
                alignedResult = whisperx.align(result["segments"], modelA, metadata, audio, self.device, return_char_alignments=False)
            except Exception as e:
                print(f"Failed to align {track['title']}: {e}")
                continue

            whisperWords = []
            for segment in alignedResult["segments"]:
                for word in segment.get("words", []):
                    if "start" in word and "end" in word:
                        text = word.get("word") if "word" in word else word.get("text")
                        whisperWords.append({
                            "start": word["start"],
                            "end": word["end"],
                            "word": self.cleanText(text)
                        })

            officialCleaned = [self.cleanText(word.get("word", "")) for word in officialWords]
            whisperCleaned = [word["word"] for word in whisperWords]

            matcher = SequenceMatcher(None, officialCleaned, whisperCleaned)
            verifiedWords = []
            pruned = 0

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    for offset in range(i2-i1):
                        offIdx = i1 +offset
                        whIdx = j1 + offset

                        originalStart = float(officialWords[offIdx]["start"])
                        whStart = float(whisperWords[whIdx]["start"])

                        if abs(whStart - originalStart) <= tolerance:
                            verifiedWords.append({
                                "word": officialWords[offIdx]["word"],
                                "start": round(whStart, 4),
                                "end": round(float(whisperWords[whIdx]["end"], 4))
                            })
                        else:
                            verifiedWords.append(officialWords[offIdx])
                else:
                    for offset in range(i2-i1):
                        verifiedWords.append(officialWords[i1+offset])

            track["words"] = sorted(verifiedWords, key=lambda x: x.get("start", 0))
            track["verified"] = True
            self.saveProgress(manifestPath, tempOutputPath, track)
        return True


    def isAlreadyChecked(self, track):
        return track.get("verified", False)

    def cleanAll(self, nthreads=3):
        processedDir = os.path.join(self.musicDir, "Processed")
        artists = [directory for directory in os.listdir(processedDir) if os.path.isdir(os.path.join(processedDir, directory))]

        if not artists:
            print(f"No artists found in {processedDir}")

        with ThreadPoolExecutor(max_workers=nthreads) as executor:
            futureToArtist = {
                executor.submit(self.cleanAristCorpus, artist): artist for artist in artists
            }
            for future in as_completed(futureToArtist):
                artistName = futureToArtist[future]
                try:
                    success = future.result()
                    if success:
                        print(f"Job for {artistName} completed successfully")
                except Exception as e:
                    print(f"Failed to clean {artistName}: {e}")

if __name__ == "__main__":
    cleaner = Cleaner()
    cleaner.cleanAll(nthreads=2)