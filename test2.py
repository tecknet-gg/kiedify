import time
from downloader import Downloader
from directory import DirectoryManager
from isolater import Preprocessor
from lyrics import LyricFinder

def main():
    artists = ["Weezer", "Beatles", "Red Hot Chilli Peppers", "Paramore", "Avril Lavigne", "Laufey"]
    # artists = []
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

    print(f"Download time: {round(timeEnd - timeStart, 2)} Successful: {passed} Failed: {failed}")
    if passed != 0:
        print(f"Time per song:{round((timeEnd - timeStart) / passed, 2)}")

    processor = Preprocessor()
    processor.generateQueue()
    processor.processMulithreaded(nthread=4)

    manager = DirectoryManager(musicDir)
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()

    lyrics = LyricFinder()
    lyrics.ammendMetadata()
    lyrics.injectDuration()
    lyrics.generateQueue()
    lyrics.gatherMulithreaded(nthread=5)
    lyrics.cleanLyricless()

    manager.nukeTarget("Raw")
    manager.nukeTarget("Processed")


    print("Done!")

def helper():
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Trying again...")
        helper()

if __name__ == "__main__":
    helper()
