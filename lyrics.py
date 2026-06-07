import json
import os
import threading
from queue import Queue, Empty
import requests
from mutagen.mp3 import MP3


class LyricFinder:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = musicDir
        self.lyricsQueue = Queue()

        self.lock = threading.Lock()
        self.URL = "https://lrclib.net/api/get"

        self.headers = {
            "User-Agent": "kiedify/v0.1 (https://github.com/tecknet-gg/kiedify; <hattijeevan@gmail.com>)",
        }

        print("Initialised")


    def cleanString(self, text):
        if not text:
            return ""

        clean = text.lower()

        clean = clean.replace("&", "and")
        clean = "".join(char for char in clean if char.isalnum())
        return clean


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

                trackEntry = next((track for track in tracks if track.get("title") == title), None)
                if not trackEntry:
                    clean = self.cleanString(title)
                    trackEntry = next((track for track in tracks if self.cleanString(track.get("title")) == clean), None)

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
        while True:
            try:
                songName, artist, duration = self.lyricsQueue.get(timeout=1)
            except Empty:
                print("Queue empty, exiting.")
                return

            try:
                data = self.queryLyric(songName, artist, duration)
                if data:
                    self.saveToJson(artist, songName, data)
                else:
                    print(f"No lyrics found for {songName}")
            except Exception as e:
                print(f"Failed to query lyric server: {e}")
                continue
            finally:
                self.lyricsQueue.task_done()


    def parseSyncedLyrics(self, lyrics):
        parsedLyrics = []
        raw = lyrics.strip().split("\n")
        for line in raw:
            line = line.strip()
            if not line or not line.startswith("["):
                continue

            try:
                time, text = line.split("]", 1)
                time = time.strip("[").strip()
                text = text.strip()

                if not text:
                    continue

                parts = time.split(":")
                minutes = float(parts[0])
                seconds = float(parts[1])
                start = round(minutes * 60 + seconds, 2)

                parsedLyrics.append({
                    "start": start,
                    "text": text,
                    "words": text.split()
                })


            except Exception as e:
                print(f"Failed to parse synced lyrics: {e}")
                continue

        final = []
        for i in range(len(parsedLyrics) - 1):
            if i < len(parsedLyrics) - 1:

                current["end"] = parsedLyrics[i+1]["start"]
                current["duration"] = round(current["end"] - current["start"], 2)

                if current["text"]:
                    final.append(current)

            else:
                if current["text"]:
                    current["end"] = current["start"]+3.0
                    current["duration"] = 3.0
                    final.append(current)



        return final


    def saveToJson(self, artist, songName, lyricData):
        artistPath = os.path.join(self.musicDir, "Processed", artist)
        manifestPath = os.path.join(artistPath, f"{artist}.json")

        if not os.path.exists(manifestPath):
            print(f"Missing artist manifest: {artist}")
            return

        with self.lock:
            try:
                with open(manifestPath, "r") as f:
                    tracks = json.load(f)
            except Exception as e:
                print(f"Failed to load {manifestPath}: error: {e}")
                return

            manifestUpdated = False
            cleanTarget = self.cleanString(songName)

            for track in tracks:
                if self.cleanString(track.get("title")) == cleanTarget:
                    synced = lyricData.get("syncedLyrics")
                    plain = lyricData.get("plainLyrics")
                    id = lyricData.get("id")


                    if synced:
                        parsed = self.parseSyncedLyrics(synced)
                        for line in parsed:
                            line["id"] = id

                            track["lyrics"] = parsed
                            track["lyricsFound"] = True
                            track["syncedLyrics"] = True
                            print(f"Synced lyrics found for {songName}")

                    elif plain:
                        track["lyrics"] = [{
                            "id": id,
                            "text": plain,
                        }]
                        track["lyricsFound"] = True
                        track["syncedLyrics"] = False
                        print(f"Synced lyrics missing for {songName}")

                    else:
                        print(f"No lyrics found for {songName}")

                    track["lyricsPath"] = os.path.join(artistPath, f"{songName}.json")
                    manifestUpdated = True
                    print("Lyrics saved")
                    break

        if manifestUpdated:
            try:
                with open(manifestPath, "w") as f:
                    json.dump(tracks, f, indent=4)
                print("Manifest succesfully updated")
            except Exception as e:
                print(f"Failed to save {manifestPath}: error: {e}")


    def queryLyric(self, songName, artist, duration):

        if duration:
            payload = {
                "artist": artist,
                "song": songName,
                "duration": int(duration),
            }
        else:
            payload = {
                "artist": artist,
                "song": songName,
            }


        response = requests.get(self.URL, headers=self.headers, params=payload)
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
                                duration = track.get("duration")
                                if duration:
                                    self.lyricsQueue.put((track["title"], track["artist"], duration))
                                else:
                                    print(f"Missing duration for {track['title']}")
                                    self.lyricsQueue.put((track["title"], track["artist"], None))

    def testQueue(self):
        self.generateQueue()
        while not self.lyricsQueue.empty():
            try:
                item = self.lyricsQueue.get()
                print(item)
                self.lyricsQueue.task_done()
            except KeyError:
                print("Missing data, skipping.")







if __name__ == "__main__":
    lyricFinder = LyricFinder()
    lyricFinder.ammendMetadata()
    lyricFinder.injectDuration()
