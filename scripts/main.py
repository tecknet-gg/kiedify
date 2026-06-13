from directory import DirectoryManager
from downloader import Downloader
from isolater import Preprocessor
from lyrics import LyricFinder
from searcher import Searcher
from syncer import Syncer
from stitcher import Stitcher
import os


currentPath = os.path.abspath(__file__)
dir = os.path.join(os.path.dirname(os.path.dirname(currentPath)), "Music")
print(dir)



def aristPipeline(artist, qty=10):

    manager = DirectoryManager(dir)
    downloader = Downloader(dir)
    preprocessor = Preprocessor(dir)
    lyricFinder = LyricFinder(dir)
    searcher = Searcher(dir)
    syncer = Syncer(dir)
    stitcher = Stitcher(dir)

    albums = downloader.getDiscog(artist, qty=qty)
    preprocessor.generateQueue()
    preprocessor.processMulithreaded(nthread=4)
    manager.flattenProcessedDir()
    lyricFinder.generateQueue()
    lyricFinder.gatherMulithreaded(nthread=5)
    lyricFinder.cleanLyricless()
    syncer.syncAll()
    manager.cleanIsolatedDir()
    manager.cleanDownloadDir()
    manager.cleanRawDir()

if __name__ == "__main__":
    print(f"Weezer, Red Hot Chilli Peppers, The Beatles, Paramore, Avril Lavigne, The Cardigans")
    query = input("Enter the query: ")
    artist = input("Enter the artist: ")

    searcher = Searcher(dir)
    stitcher = Stitcher(dir)

    stitchList = searcher.getStitchMap(query, artist)
    stitcher.generateMP3(stitchList)
