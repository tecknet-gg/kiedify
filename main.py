from downloader import Downloader
from directory import DirectoryManager
from isolater import Preprocessor

import time
import os

'''
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
    processor.generateQueue2()
    processor.processMulithreaded(nthread=4)
    manager = DirectoryManager(musicDir)
    manager.cleanIsolatedDir()
    manager.flattenProcessedDir()
'''

if __name__ == "__main__":
    manager = DirectoryManager()
    manager.flattenProcessedDir()
