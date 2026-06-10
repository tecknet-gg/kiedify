import json
import os
import torch
import whisperx


class Syncer:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music", modelSize = "base", device = "cpu", computeType = "int16"):

        self.musicDir = musicDir
        self.device = device
        self.align, self.metadata = whisperx.load_align_model(language_code="en", device=self.device)
        print(f"Loaded mode on {self.device}")

    def syncAll(self):
        processedDir = os.path.join(self.musicDir, "Processed2")

        if not os.path.exists(processedDir):
            print("Directory missing")
            return

        for artist in os.listdir(processedDir):
            artistPath = os.path.join(processedDir, artist)
            if not os.path.isdir(artistPath):
                continue

            oldManifest = os.path.join(artistPath, f"{artist}.json")
            if not os.path.exists(oldManifest):
                print(f"Manifest missing for {artist}")
                continue

            print(f"Syncing {artist}")
            self.processArtist(artist, artistPath, oldManifest)

        print("Syncing finished")



    def processArtist(self, artistName, artistPath, oldManifest):
        try:
            with open(oldManifest, "r") as f:
                oldTracks = json.load(f)
        except Exception as e:
            print(f"Failed to load manifest for {artistName}: {e}")
            return

        newManifest = []

        for track in oldTracks:
            title = track.get("title")

            lyrics = track.get("lyrics")
            if not lyrics or not track.get("lyricsPath"):
                print(f"Skipping {title}, no lyrics found")
                continue

            audio = track.get("lyricsPath")
            if not audio or not os.path.exists(audio):
                print(f"Skipping {title}, no audio found")
                continue

            print(f"Aliging lyrics for {title}")
            wordTimestamps = self.generateWordTimestamps(audio, lyrics)

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

            newManifest.append(syncedData)
            newManifestPath = os.path.join(artistPath, f"{artistName}Synced.json")
            try:
                with open(newManifestPath, "w") as f:
                    json.dump(syncedData, f, indent=4)
                print(f"Synced manifest saved for {title}")
            except Exception as e:
                print(f"Failed to save synced manifest for {title}: {e}")

    def generateWordTimestamps(self, audioPath, lyrics):
        words = []
        try:
            segments = []
            for line in lyrics:
                if "text" in line and "start" in line and "end" in line:
                    segments.append({
                        "text": line["text"],
                        "start": line["start"],
                        "end": line["end"],
                    })

            if not segments:
                print(f"No segments found in lyrics for {title}")
                return

            audio = whisperx.load_audio(audioPath)

            alignedResults = whisperx.align(segments, self.align, self.metadata, audio, self.device)  # char alignments maybe?

            for segment in alignedResults:
                if "words" not in segment:
                    continue

                for word in segment["words"]:
                    if "start" in w and "end" in word:
                        words.append({
                            "word": word["word"],
                            "start": round(float(word["start"], 2)),
                            "end": round(float(word["end"]), 2)
                        })

        except Exception as e:
            print(f"Failed to generate word timestamps for {title}: {e}")
            return []
        print(words)
        return words

if __name__ == "__main__":
    syncer = Syncer()
    syncer.syncAll()








