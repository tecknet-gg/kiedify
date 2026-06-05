import requests
from queue import Queue
import yt_dlp
import json
import os
import threading
import time

class Downloader:
    def __init__(self):
        self.baseURL = "https://api.deezer.com"
        self.musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"
        self.config = {}
        self.installQueue = Queue()
        self.passed = 0
        self.failed = 0
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print("Config file missing")
        except json.decoder.JSONDecodeError:
            print("Config file invalid")

        self.config = self.config.get("opt",{})


        print("Initialised")

    def getArtist(self, artist):
        url = f"{self.baseURL}/search/artist"
        res = requests.get(url, params={"q": artist}).json()

        return res["data"][0]

    def getTopAlbums(self, artist):
        artist = self.getArtist(artist)
        artistID = artist["id"]

        url = f"{self.baseURL}/artist/{artistID}/albums"
        res = requests.get(url, params={"limit": 100}).json()

        albums = []

        for a in res["data"]:
            albums.append({"id": a["id"], "title": a["title"], "rank": a.get("fans", 0)})

        albums.sort(key=self.sortByRank, reverse=True)

        return albums

    def sortByRank(self, item):
        return item["rank"]

    def prettyPrint(self, albums):
        print("Top albums:")
        for i, a in enumerate(albums, 1):
            print(f"{i}. {a['title']}")

    def cleanDiscography(self, albums):
        targets = ["version", "deluxe", "live", "compilation", "best", "hits", "commercial", "remix", "acoustic", "international", "practice", "session", "anniversary"]
        clean = []
        for a in albums:
            title = a["title"].lower()
            if not(any(elem in title for elem in targets)):
                clean.append(a)

        return clean

    def getDiscog(self, artist, qty=10):
        albums = self.getTopAlbums(artist)
        albums = self.cleanDiscography(albums)

        finalAlbums = []
        length = len(albums) if len(albums) < qty else qty

        for i in range(0, length):
            finalAlbums.append(albums[i])

        return finalAlbums

    def getTrackList(self, album):
        url = f"{self.baseURL}/album/{album['id']}"
        data = requests.get(url).json()
        tracks = data["tracks"]["data"]
        for track in tracks:
            print(f"Title: {track['title']} Artist: {track['artist']['name']} Link: {track['link']} Album: {track['album']['title']}")
        return tracks

    def assembleInstallQueue(self, tracks):
        queue = Queue()
        for track in tracks:
            queue.put(track)
        return queue

    def installTracks(self, queue):
        while not queue.empty():
            track = queue.get()

            title = track["title"]
            artist = track["artist"]["name"]
            album = track["album"]["title"]

            query = f"{title} - {artist} Official Music Video"
            outputDir= os.path.join(f"{self.musicDir}/{artist}/{album}",f"{title}.%(ext)s")
            opts = self.config.copy()
            opts["outtmpl"] = outputDir

            searchURL = f"ytsearch:{query}"
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    ydl.download([searchURL])
                    self.passed += 1
                except yt_dlp.DownloadError as error:
                    print(f"Error downloading {title}: {error}")
                    self.failed += 1

    def artistToInstalled(self, artist, qty=10, nthreads=3):
        albums = self.getDiscog(artist,qty=qty)
        self.prettyPrint(albums)
        self.passed = 0
        self.failed = 0

        for album in albums:
            tracks = self.getTrackList(album)
            for track in tracks:
                self.installQueue.put(track)

        threads = []
        for i in range(nthreads):
            thread = threading.Thread(target=self.installWorker)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return self.passed, self.failed

    def installWorker(self):
        self.installTracks(self.installQueue)



if __name__ == "__main__":
    artist = input("Enter the artist: ")

    timeStart = time.perf_counter()
    downloader = Downloader()
    passed, failed = downloader.artistToInstalled(artist, qty=1, nthreads=10)
    timeEnd = time.perf_counter()
    print(f"Download time: {round(timeEnd - timeStart, 2) } Successful: {passed} Failed: {failed}")
    if passed!=0:
        print(f"Time per song:{round((timeEnd - timeStart)/passed, 2)}")

