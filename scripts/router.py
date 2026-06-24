import os
from cgitb import text

from matplotlib import artist

from phoneme import PhonemeSynth, PhonemeExtractor, PhonemeNode
from stitcher import Stitcher
from searcher import Searcher
from downloader import Downloader
from isolater import Preprocessor
from directory import DirectoryManager
from lyrics import LyricFinder

class Router:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music", globalNodes=None, weights=None):

        self.globalNodes = globalNodes if globalNodes else None
        self.musicDir = dir
        self.extractor = PhonemeExtractor(self.musicDir)
        self.weights = self.extractor.phonemeWeights

        self.synth = PhonemeSynth(self.musicDir, self.globalNodes, weights=self.weights)
        self.phoneme = PhonemeExtractor(dir=self.musicDir)
        self.stitcher = Stitcher(dir=self.musicDir)
        self.searcher = Searcher(dir=self.musicDir)
        self.downloader = Downloader(dir=self.musicDir)
        self.preprocessor = Preprocessor(dir=self.musicDir)
        self.manager = DirectoryManager(dir=self.musicDir)
        self.lyrics = LyricFinder(dir=self.musicDir)

    def basicMatch(self, text, artist, fuzzy=True, rtc=True):
        if fuzzy:
            stitchMap = self.searcher.basicMatch(text, artist, mode="fuzzy")
        else:
            stitchMap = self.searcher.basicMatch(text, artist, mode="exact")
        file = self.stitcher.generateMP3(stitchMap)
        print(f"Generated {file}")
        return file

    def semanticMatch(self, text, artist):
        stitchMap = self.searcher.semanticMatch(text, artist)
        file = self.stitcher.generateMP3(stitchMap)
        print(f"Generated {file}")
        return file

    def phonemeMatch(self, text, artist):
        stitchMap = self.synth.runCorpus(text, artist)
        if not stitchMap:
            print("No stitch map generated")
            return
        file = self.stitcher.generateMP3(stitchMap)
        print(f"Generated {file}")

    def downloadArists(self, artists):
        self.downloader.downloadArists(artists)

    def processAll(self, nthreads=2):
        self.preprocessor.processAll(max=nthreads)
        self.manager.cleanDownloadDir()
        self.manager.cleanIsolatedDir()
        self.manager.flattenProcessedDir()

    def sourceLyrics(self, nthreads=5):
        self.lyrics.ammendMetadata()
        self.lyrics.injectDuration()
        self.lyrics.generateLyrics()
        self.lyrics.gatherMulithreaded(nthreads=nthreads)
        self.lyrics.cleanLyricless()

    def postClean(self):
        self.manager.nukeTarget("Raw")
        self.manager.nukeTarget("Processed")

    def stageMFA(self, artist):
        self.phoneme.prepareMFA(artist)

    def generateArist(self, artist):
        self.phoneme.prepareMFA(artist)
        success = self.phoneme.runMFA(artist)
        return success

if __name__ == "__main__":
    router = Router()
    router.phonemeMatch("I'm a little teapot", "Weezer")
