import os
from phoneme import PhonemeSynth, PhonemeExtractor, PhonemeNode
from stitcher import Stitcher
from searcher import Searcher

class Router:
    def __init__(self, globalNodes=None, semanticEngine=None, basicDB=None, weights=None):

        self.globalNodes = globalNodes if globalNodes else None
        self.semanticEngine = semanticEngine
        self.basicDB = basicDB

        self.extractor = PhonemeExtractor()
        self.weights = weights if weights else self.extractor.phonemeWeights
        self.musicDir = self.extractor.musicDir

        self.synth = PhonemeSynth(self.musicDir, self.globalNodes, weights=self.weights)
        self.stitcher = Stitcher(dir=self.musicDir)
        self.searcher = Searcher(dir=self.musicDir)

    def basicMatch(self, text, artist, fuzzy=True, rtc=True):
        if fuzzy:
            stitchMap = self.searcher.basicMatch(text, artist, mode="fuzzy", rtc=True)
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

if __name__ == "__main__":
    router = Router()
    router.phonemeMatch("hey hello how are you", "Weezer")