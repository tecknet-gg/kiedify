import os
from cgitb import text
from phoneme import PhonemeSynth, PhonemeExtractor, PhonemeNode
from stitcher import Stitcher
from searcher import Searcher
from downloader import Downloader
from isolater import Preprocessor
from directory import DirectoryManager
from lyrics import LyricFinder
from tts import TTSGenerator
from inference import TTS
from cleaner import Cleaner
from syncer import Syncer
from rvc import RVCGenerator
from dataset import DatasetGenerator

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
        self.ttsgenerator = TTSGenerator(dir=self.musicDir)
        self.tts = TTS(dir=self.musicDir)
        self.syncer = Syncer(dir=self.musicDir)
        #self.cleaner = Cleaner(dir=self.musicDir)
        self.rvcgenerator = RVCGenerator(dir=self.musicDir)
        self.dataset = DatasetGenerator(dir=self.musicDir)

    def basicMatch(self, text, artist, fuzzy=True, patchingMode=None, rtc=True):
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
        self.downloader.queueArtists(artists)

    def preprocessAll(self, nthreads=2):
        self.preprocessor.processAll(max=nthreads)
        self.manager.cleanDownloadDir()
        self.manager.cleanIsolatedDir()
        self.manager.flattenProcessedDir()

    def sourceLyrics(self, nthreads=5):
        self.lyrics.ammendMetadata()
        self.lyrics.injectDuration()
        self.lyrics.generateQueue()
        self.lyrics.gatherMulithreaded(nthreads=nthreads)
        self.lyrics.cleanLyricless()

    def postClean(self):
        self.manager.nukeTarget("Raw")
        self.manager.nukeTarget("Processed")

    def stageMFA(self, artist):
        self.phoneme.prepareMFA(artist)

    def generateArtist(self, artist):
        self.phoneme.prepareMFA(artist)
        success = self.phoneme.runMFA(artist)
        return success

    def generateTTSDataset(self, artist):
        self.ttsgenerator.generateTTSDataset(artist)

    def exportONNX(self, artist):
        self.ttsgenerator.exportModel(artist)

    def pruneTTSDataset(self, artists):
        for artist in artists:
            self.ttsgenerator.pruneTTSDataset(artist)

    def downloadTTSBases(self):
        self.ttsgenerator.downloadBases()

    def generateTTSModel(self, artist, gender, resume=True):
        self.ttsgenerator.generateModel(artist, gender, resume=resume)

    def tts(self, text, artist, fileName=None):
        self.tts.synthesise(text, artist, fileName=fileName)

    def secondPass(self, nthreads=3):
        self.cleaner.cleanAll(nthreads=nthreads)

    def syncAll(self):
        self.syncer.syncAll()

    def downloadRVCBases(self):
        self.rvcgenerator.downloadBases()

    def generateDatasets(self, artists):
        for artist in artists:
            self.dataset.generateDataset(artist)

    def pruneDataset(self, artists):
        for artist in artists:
            self.generator.pruneDataset(artist)


if __name__ == "__main__":
    router = Router()
    artists = ["Weezer", "Red Hot Chili Peppers", "The Pretenders", "Fleetwood Mac"]
    gender = ["male", "male", "female", "female"]

    #router.downloadArists(artists)
    router.preprocessAll()
    router.sourceLyrics()
    router.postClean()
    router.syncAll()

    #router.secondPass()
    #router.generateTTSDataset(artists)
    #router.pruneTTSDataset(artists)
    #router.downloadTTSBases()

    #router.generateTTSModel(artists[0], gender[0])
    #router.exportONNX(artists[0])


