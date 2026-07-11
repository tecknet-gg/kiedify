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
from ttsinference import TTS
from syncer import Syncer
from dataset import DatasetGenerator
import subprocess
import re

class Router:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music", globalNodes=None, weights=None, artists=None):

        self.globalNodes = globalNodes if globalNodes else None
        self.musicDir = dir
        self.extractor = PhonemeExtractor(self.musicDir)
        self.weights = self.extractor.phonemeWeights

        self.artistMetadata = artists if artists else None
        self.artists = []
        self.genders = []

        for artist, gender in self.artistMetadata:
            self.artists.append(artist)
            self.genders.append(gender)

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
        self.dataset = DatasetGenerator(dir=self.musicDir)

    def basicMatch(self, text, artist, fuzzy=True, patchingMode=None):
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

    def downloadArtists(self, artists, qty=10):
        self.downloader.queueArtists(artists, qty=qty)

    def preprocessAll(self, nthreads=2):
        self.preprocessor.processAll(max=nthreads)
        self.manager.cleanDownloadDir()
        self.manager.cleanIsolatedDir()

    def sourceLyrics(self, nthreads=15):
        self.lyrics.generateQueue()
        self.lyrics.gatherMulithreaded(nthreads=nthreads)
        self.lyrics.cleanLyricless()

    def ammendMetadata(self):
        self.manager.flattenProcessedDir()
        self.lyrics.ammendMetadata()
        self.lyrics.injectDuration()

    def postClean(self):
        self.manager.nukeTarget("Raw")
        self.manager.nukeTarget("Isolated")

    def nukeTarget(self, target):
        self.manager.nukeTarget(target)

    def stageMFA(self, artist):
        self.phoneme.prepareMFA(artist)

    def generateArtist(self, artist):
        self.phoneme.prepareMFA(artist)
        success = self.phoneme.runMFA(artist)
        return success

    def exportONNX(self, artist):
        self.ttsgenerator.exportModel(artist)

    def downloadTTSBases(self):
        self.ttsgenerator.downloadBases()

    def generateTTSModel(self, artist, gender, resume=True):
        self.ttsgenerator.generateModel(artist, gender, resume=resume)

    def tts(self, text, artist, fileName=None):
        self.tts.synthesise(text, artist, fileName=fileName)

    def secondPass(self, nthreads=3):
        from cleaner import Cleaner
        self.cleaner = Cleaner(dir=self.musicDir)
        self.cleaner.cleanAll(nthreads=nthreads)

    def syncAll(self):
        self.syncer.syncAll()

    def downloadRVCBases(self):
        self.rvcgenerator.downloadBases()

    def generateDatasets(self, artists):
        for artist in artists:
            self.dataset.generateDataset(artist)

    def pruneDataset(self, artists, target):
        for artist in artists:
            self.dataset.pruneDataset(artist, target=target)

    def rvc(self, text, artist, fileName="output.txt", ttsMode="local"):
        artistKey = artist.lower()
        gender = self.genders[self.artists.index(artist)]

        sitchedDir = os.path.join(self.musicDir, "Stitched")
        os.makedirs(sitchedDir, exist_ok=True)

        ttsTemp = f"{fileName}_temp"

        ttsWav = os.path.join(sitchedDir, f"{ttsTemp}.wav")
        finalRVCWav = os.path.join(sitchedDir, f"{fileName}.wav")
        finalRVCMP3 = os.path.join(sitchedDir, f"{fileName}.mp3")


        print(f"Generate base tts: {ttsTemp}")
        self.tts.synthesise(text, artist, fileName=ttsWav)

        rootDir = self.musicDir.rsplit("/", 1)[0]
        rvcPython = os.path.join(rootDir, "venvRVC", "bin", "python")
        workerScript = os.path.join(rootDir, "scripts", "rvcinference.py")


        pitch = 0
        if gender == "female":
            pitch = 0
        if gender == "male":
            pitch = 0


        cmd = [
            rvcPython, workerScript,
            "--artist", artist.lower(),
            "--input", ttsWav,
            "--output", finalRVCWav,
            "--pitch", str(pitch),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Generated {finalRVCWav}")
            if os.path.exists(finalRVCWav):

                ffmpegCmd = [
                    "ffmpeg", "-y",
                    "-i", finalRVCWav,
                    "-c:a", "libmp3lame",
                    "-q:a", "2",
                    finalRVCMP3,
                ]
                subprocess.run(ffmpegCmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(finalRVCWav)
                if os.path.exists(ttsWav):
                    os.remove(ttsWav)

                print(f"Exported {finalRVCWav} as {finalRVCMP3}")
                return finalRVCMP3
            else:
                print(f"Conversion subprocess ran, but no output file found")
                return False


        except subprocess.CalledProcessError as e:
            print(f"Error generating {finalRVCWav} - {e}")
            return False

    def apiMatch(self, text, artist, patching=True, mode="fuzzy"):
        pass

    #make sure you hint to the existence of TTS, Phoneme Graph Traversal and Semantic Matching, but not exposed to the API due to compute




if __name__ == "__main__":
    artists = ["Weezer", "Red Hot Chili Peppers","The Dismemberment Plan", "The Pretenders", "Fleetwood Mac", "Paramore"]
    genders = ["male", "male", "male", "female", "female", "female"]
    artistsMeta = tuple(zip(artists, genders))
    router = Router(artists=artistsMeta)
    #router.rvc("The Pretenders", "The Pretenders")

    #router.downloadArtists(artists[5:], qty=5)

    #router.preprocessAll(nthreads=2)

    #router.ammendMetadata()
    #router.sourceLyrics()

    #router.postClean()

    #router.syncAll()


    #router.secondPass()

    #router.generateDatasets(artists)
    #router.pruneDataset(artists, target=1)
    #router.downloadRVCBases()

    #router.basicMatch(text="lets try that again shall we", artist="Weezer")

    '''
    for i, artist in enumerate(artists):
        router.generateTTSModel(artist, genders[i])
        router.exportONNX(artist)
    '''

    #router.nukeTarget("Dataset")
    #router.generateDataset(artists)
    #router.pruneDataset(artists, target=1)

    '''
    for i, artist in enumerate(artists):
        router.generateRVCModel(artist)
    '''



