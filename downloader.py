import requests
from queue import Queue
import yt_dlp
import json
import os
import shutil
import threading
import time
from isolater import Preprocessor
from directory import DirectoryManager

class Downloader:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.baseURL = "https://api.deezer.com"
        self.rawDir = os.path.join(musicDir,"Raw")
        self.config = {}
        self.installQueue = Queue()
        self.manager = DirectoryManager(musicDir)

        self.passed = 0
        self.failed = 0

        try: # loading config files
            with open("config.json", "r") as configFile:
                self.config = json.load(configFile)
        except FileNotFoundError:
            print("Configuration file not found.")
        except json.decoder.JSONDecodeError:
            print("Configuration file is not valid JSON.")

        self.config = self.config.get("opt",{})

        print("Initialised")

    def getArtist(self, artist):
        URL = f"{self.baseURL}/search/artist/"
        result = requests.get(URL, params={"q": artist}).json() #querying artist from deezer
        return result["data"][0]

    def prettyPrint(self, albums):
        print("Top Albums")
        for i, album in enumerate(albums):
            print(f"[{i+1}] - {album['title']}")

    def cleanDiscography(self, albums):
        targets = ["version", "deluxe", "live", "compilation", "best", "hits", "commercial", "remix", "acoustic", "international", "practice", "session", "anniversary"]
        clean = []
        for album in albums:
            title = album["title"].lower()
            if not(any(elem in title for elem in targets)): #removes albums with said words
                clean.append(album)
        return clean

    def getDiscog(self, artist, qty=10):
        albums = self.getTopAlbums(artist)
        albums = self.cleanDiscography(albums)

        finalAlbums = []
        length = len(albums) if len(albums) < qty else qty

        for i in range(0, length):
            finalAlbums.append(albums[i])

        return finalAlbums

    def getTopAlbums(self, artist):

        artist = self.getArtist(artist) #get top albums
        artistID = artist["id"]

        URL = f"{self.baseURL}/artist/{artistID}/albums"
        result = requests.get(URL, params={"limit": 100}).json()

        albums = []
        for album in result["data"]:
            albums.append({"id": album["id"], "title": album["title"], "rank": album.get("fans", 0)})

        albums.sort(key=self.sortByRank, reverse=True)

        return albums

    def sortByRank(self, album):
        return album["rank"]

    def assembleInstallQueue(self):
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
            deezerId = track["id"]

            query = f"{title} - {artist} Official Music Video"
            outputDir = os.path.join(f"{self.rawDir}/{artist}/{album}", f"{title}")

            options = self.config.copy()
            options["outtmpl"] = outputDir

            searchURL = f"ytsearch:{query}"
            with yt_dlp.YoutubeDL(options) as ydl:
                try:
                    ydl.download([searchURL])
                    print(f"Successfully downloaded {title}")
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

        print("Cleaning output")

        self.manager.cleanDownloadDir()


        print("Done!")

        return self.passed, self.failed

    def getTrackList(self, album):
        URL = f"{self.baseURL}/album/{album['id']}"
        data = requests.get(URL).json()
        tracks = data["tracks"]["data"]

        trackList = []
        for track in tracks:
            print(f"Title: {track['title']} Artist: {track['artist']['name']} Link: {track['link']} Album: {track['album']['title']}")
            trackList.append({
                "title": track["title"],
                "artist": track["artist"]["name"],
                "album": track["album"]["title"],
                "id": track["id"]
            })

        artistName = album.get("artist", {}).get("name", trackList[0]["artist"]) if trackList else "Unknown"
        albumDir = os.path.join(self.rawDir, artistName, album["title"])

        os.makedirs(albumDir, exist_ok=True)
        targetFile = os.path.join(albumDir, f"{album['title']}.json")


        try:
            with open(targetFile, "w") as f:
                json.dump(trackList, f, indent=4)
            print(f"Successfully wrote to {targetFile}")
        except Exception as e:
            print(f"Error writing to {targetFile}: {e}")

        return tracks

    def installWorker(self):
        self.installTracks(self.installQueue)


    def queueArtists(self,artists, qty=10, nthreads=3):
        passed, failed = 0, 0
        for artist in artists:
            passed, failed  = self.artistToInstalled(artist, qty=qty, nthreads=nthreads)
            self.passed += passed
            self.failed += failed
        return self.passed, self.failed



if __name__ == "__main__":
    #artists = ["Weezer", "Beatles", "Red Hot Chilli Peppers", "Paramore", "Avril Lavigne", "Laufey" ]
    artists = []
    if len(artists) == 0:
        artist = input("Enter the artist: ")
        numberAlbums = int(input("Enter the number of albums: "))
        timeStart = time.perf_counter()
        downloader = Downloader()
        passed, failed = downloader.artistToInstalled(artist, qty=numberAlbums, nthreads=15)
        timeEnd = time.perf_counter()
    else:
        timeStart = time.perf_counter()
        downloader = Downloader()
        passed, failed = downloader.queueArtists(artists, qty=10, nthreads=25)
        timeEnd = time.perf_counter()

    print(f"Download time: {round(timeEnd - timeStart, 2) } Successful: {passed} Failed: {failed}")
    if passed!=0:
        print(f"Time per song:{round((timeEnd - timeStart)/passed, 2)}")


    processor = Preprocessor()
    processor.generateQueue()
    processor.processMulithreaded(nthread=4)
    manager = DirectoryManager(musicDir)
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()
