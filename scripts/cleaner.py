import os
import whisperx
import re
import torch
import json
from concurrent.futures import ThreadPoolExecutor, as_completed




class Cleaner:
    def __init__(self, musicDir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = musicDir

        self.device = "cpu" #you should probably change this to cuda if your setup supports that

        computeType = "float32" #float16 if cuda
        self.model = whisperx.load_model("large-v2", device=self.device, compute_type=computeType)

    def cleanText(self, text):
        text = text.lower().strip()
        text = re.sub(r'[()\[\]{}.,!?;\"]', '', text)
        return text.replace('-', ' ')

    def cleanAristCorpus(self, artist, tolerance=0.75):

        processedDir = os.path.join(self.musicDir, "Processed4", artist)
        manifestPath = os.path.join(processedDir, f"{artist}.json")
        tempOutputPath = os.path.join(processedDir, f"{artist}Synced.tmp")

        if not os.path.exists(manifestPath):
            print(f"Manifest missing for {artist}")
            return False

        with open(manifestPath, "r") as f:
            tracks = json.load(f)

        cleanedTracks = []
        print(f"Cleaning {artist}'s corpus")

        for track in tracks:
            title = track.get("title")
            officialWords = track.get("words", [])
            audioPath = os.path.join(processedDir, f"{title}.mp3")

            if not audioPath or not os.path.exists(audioPath):
                print(f"Audio file missing for {track['title']}")
                continue


            print(f"Cleaning {track['title']}")

            audio = whisperx.load_audio(audioPath)
            result = self.model.transcribe(audio, batch_size=16)

            try:
                modelA, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
                alignedResult = whisperx.align(result["segments"], modelA, metadata, audio, self.device, return_char_alignments=False)
            except Exception as e:
                print(f"Failed to align {track['title']}: {e}")
                continue

            whisperWords = []
            for segment in alignedResult["segments"]:
                for word in segment.get("words", []):
                    if "start" in word and "end" in word:
                        whisperWords.append({
                            "start": word["start"],
                            "end": word["end"],
                            "word": word["word"]
                        })

            verifiedWords = []
            pruned = 0

            for official in officialWords:
                word = self.cleanText(official.get("word", ""))
                start = float(official.get("start", 0.0))

                if not official:
                    continue

                match = None
                for tw in whisperWords:
                    if tw["word"] == word and abs(tw["start"] - start) <= tolerance:
                        match = tw
                        break

                if match:
                    verifiedWords.append({
                        "word": official["word"],
                        "start": round(match["start"], 4),
                        "end": round(match["end"], 4)
                    })
                else:
                    pruned += 1

            print(f"Pruned {pruned} words from {track['title']}")

            if verifiedWords:
                track["words"] = verifiedWords
                cleanedTracks.append(track)
        try:
            with open(tempOutputPath, "w") as f:
                json.dump(cleanedTracks, f, indent=4)

            os.replace(tempOutputPath, manifestPath)
            print(f"Synced manifest for {artist} saved")
            return True
        except Exception as e:
            print(f"Failed to save synced manifest for {artist}: {e}")
            if os.path.exists(tempOutputPath):
                os.remove(tempOutputPath)
            return False

    def cleanAll(self, nthreads=3):
        processedDir = os.path.join(self.musicDir, "Processed4")
        artists = [directory for directory in os.listdir(processedDir) if os.path.isdir(os.path.join(processedDir, directory))]

        if not artists:
            printf(f"No artists found in {processedDir}")

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