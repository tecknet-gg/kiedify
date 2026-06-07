import json
import os
import threading
from queue import Queue
import requests
from mutagen.mp3 import MP3


class LyricFinder:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = musicDir
        self.injectDuration()
        self.lyricsQueue = Queue()

        self.lock = threading.Lock()
        self.URL = "https://lrclib.net/api/get"

        self.headers = {
            "User-Agent": "kiedify/v0.1 (https://github.com/tecknet-gg/kiedify; <hattijeevan@gmail.com>)",
        }

        print("Initialised")

    def injectDuration(self):
        print("Injecting duration metadata")
        processedDir = os.path.join(self.musicDir, "Processed")

        if not os.path.exists(processedDir):
            print("Directory missing")
            return

        for artist in os.listdir(processedDir):
            artistPath = os.path.join(processedDir, artist)
            if not os.path.isdir(artistPath):
                continue

            manifestPath = os.path.join(artistPath, f"{artist}.json")
            if not os.path.exists(manifestPath):
                print(f"Manifest missing for {artist}")
                continue

            try:
                with open(manifestPath, "r") as f:
                    tracks = json.load(f)
            except Exception as e:
                print(f"Failed to load {manifestPath}: error: {e}")
                continue

            manifestUpdated = False

            for file in os.listdir(artistPath):
                if not file.endswith(".mp3"):
                    continue

                audioPath = os.path.join(artistPath, file)
                title = os.path.splitext(file)[0]
                trackEntry = next((track for track in tracks if track.get("title" ) == title), None)

                if trackEntry:
                    try:
                        duration = self.getDuration(audioPath)
                        if duration:
                            trackEntry["duration"] = duration
                            manifestUpdated = True
                            print(f"Duration injected for {title}")
                        else:
                            print(f"Failed to get duration for {title}")
                    except Exception as e:
                        print(f"Failed to gather duration for {title}: {e}")

                if manifestUpdated:
                    try:
                        with open(manifestPath, "w") as f:
                            json.dump(tracks, f, indent=4)
                        print("Manifest succesfully updated")
                    except Exception as e:
                        print(f"Failed to save {manifestPath}: error: {e}")
            print("Duration injection finished")

    def getDuration(self, audioPath):
        try:
            audio = MP3(audioPath)
            duration = round(audio.info.length, 2)
        except Exception as e:
            print(f"Failed to get duration for {audioPath}: {e}")
            duration = None

        return duration

    def ammendMetadata(self):
        print("Ammending metadata strcture")
        processedDir = os.path.join(self.musicDir, "Processed")

        if not os.path.exists(processedDir):
            print("Directory missing")
            return

        for artist in os.listdir(processedDir):
            artistPath = os.path.join(processedDir, artist)
            if not os.path.isdir(artistPath):
                continue

            manifestPath = os.path.join(artistPath, f"{artist}.json")
            if not os.path.exists(manifestPath):
                print(f"Manifest missing, skipping {artist}")
                continue
            try:
                with open(manifestPath, "r") as f:
                    tracks = json.load(f)
            except Exception as e:
                print(f"Failed to load {manifestPath}: error: {e}")

            manifestUpdated = False

            for track in tracks:
                if "lyricsFound" not in track:
                    track["lyricsFound"] = False
                    manifestUpdated = True

                if "syncedLyrics" not in track:
                    track["syncedLyrics"] = False
                    manifestUpdated = True

                if "lyricsPath" not in track:
                    track["lyricsPath"] = None
                    manifestUpdated = True

            if manifestUpdated:
                try:
                    with open(manifestPath, "w") as f:
                        json.dump(tracks, f, indent=4)
                    print("Manifest succesfully updated")
                except Exception as e:
                    print(f"Failed to save {manifestPath}: error: {e}")

        print("Metadata ammended")

    def getLyrics(self):
        pass

    def queryLyric(self, songName, artist, duration):
        payload = {
            "artist": artist,
            "song": songName,
            "duration": int(duration),
        }

        response = requests.post(self.URL, headers=self.headers, params=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to query lyric server: {response.status_code}")
            return None

    def generateQueue(self):
        dir = os.path.join(self.musicDir, "Processed")
        for root, dirs, files in os.walk(dir):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r") as f:
                        tracks = json.load(f)
                        for track in tracks:
                            if not track.get("lyricsFound"):
                                self.lyricsQueue.put((track["title"], track["artist"], track["duration"]))





if __name__ == "__main__":
    lyricFinder = LyricFinder()
    lyricFinder.injectDuration()
    lyricFinder.ammendMetadata()