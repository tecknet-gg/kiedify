import time
from downloader import Downloader
from directory import DirectoryManager
from isolater import Preprocessor
from lyrics import LyricFinder

def main():
    artists = ["Weezer", "Beatles", "Red Hot Chilli Peppers", "Paramore", "Avril Lavigne", "The Cardigans"]
    #artists = []
    musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"
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
        passed, failed = downloader.queueArtists(artists, qty=15, nthreads=25)
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



    print("Done!")

def helper():
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Sleeping then trying again...")
        time.sleep(60)
        print("Trying again...")
        helper()


def lyrics():
    musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"
    manager = DirectoryManager(musicDir)
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()

    lyrics = LyricFinder()
    lyrics.ammendMetadata()
    lyrics.injectDuration()
    lyrics.generateQueue()
    lyrics.gatherMulithreaded(nthread=5)

    manager.nukeTarget("Raw")


if __name__ == "__main__":

    timeStart = time.perf_counter()
    actualTimeStart = time.ctime()

    helper()

    timeEnd = time.perf_counter()
    actualTimeStop = time.ctime()
    elapsedTime = timeEnd - timeStart

    print(f"Total time: {elapsedTime} seconds")
    print(f"Start time: {actualTimeStart}")
    print(f"End time: {actualTimeStop}")


    #lyrics()

    '''
    musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music"

    manager = DirectoryManager(musicDir)
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()

    lyrics = LyricFinder()
    lyrics.ammendMetadata()
    lyrics.injectDuration()
    lyrics.generateQueue()
    lyrics.gatherMulithreaded(nthread=5)
    lyrics.cleanLyricless()
    '''