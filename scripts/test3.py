import os

from downloader import Downloader
from isolater import Preprocessor
from directory import DirectoryManager
from lyrics import LyricFinder
from syncer import Syncer
from searcher import Searcher
from stitcher import Stitcher
from phoneme import PhonemeExtractor, PhonemeNode, PhonemeSynth, loadIntervals
from stitcher import Stitcher

path = "/Users/jeevan/Documents/Python/MusicTTS/Music"


def run():
    extractor = PhonemeExtractor()
    weights = extractor.phonemeWeights

def loadCorpus(extractor, artistName):
    mfaDir = os.path.join(extractor.musicDir, "Processed3", artistName, "MFA")
    globalNodes = []

    if not os.path.exists(mfaDir):
        print(f"No MFA directory found for {artistName}")
        return globalNodes

    files = [file for file in os.listdir(mfaDir) if file.endswith(".TextGrid")]

    nodes = 0
    for file in files:
        fullPath = os.path.join(mfaDir, file)
        base, _ = os.path.splitext(file)

        audioPath = os.path.join(extractor.musicDir, "Processed3", artistName, f"{base}.mp3")

        intervals = loadIntervals(fullPath)

        for interval in intervals:
            node = PhonemeNode(
                nodeId = f"{nodes}",
                phoneme = interval["phoneme"],
                start = interval["start"],
                end = interval["end"],
                wordContext = interval.get("word", ""),
                songName=audioPath
            )
            globalNodes.append(node)
            nodes += 1
        print(f"Loaded {nodes} nodes for {artistName}")
        return globalNodes

def runCorpus():
    extractor = PhonemeExtractor()
    target = "Weezer"

    globalDatbase = loadCorpus(extractor, target)
    if not globalDatbase:
        print("No global database found")
        return

    synth = PhonemeSynth(globalDatbase, weights=extractor.phonemeWeights)
    text = input("Enter text: ")

    stitchMap = synth.generateStitchMap(text)
    stitcher = Stitcher(dir=extractor.musicDir)
    stitcher.generateMP3(stitchMap)


def semanticMatch():
    searcher = Searcher()
    stitcher = Stitcher()

    print(f"Weezer, Red Hot Chilli Peppers, The Beatles, Paramore, Avril Lavigne, The Cardigans")
    query = input("Enter the query: ")
    artist = input("Enter the artist: ")

    stitchList = searcher.semanticMatch(query, artist)
    stitcher.generateMP3(stitchList)

def basicMatch():
    searcher = Searcher()
    stitcher = Stitcher()

    print(f"Weezer, Red Hot Chilli Peppers, The Beatles, Paramore, Avril Lavigne, The Cardigans")
    query = input("Enter the query: ")
    artist = input("Enter the artist: ")

    stitchList = searcher.basicMatch(query, artist)
    stitcher.generateMP3(stitchList)


if __name__ == "__main__":
    print(f"1. Run corpus\n2. Semantic match\n3. Basic match")
    choice = int(input("Enter your choice: "))
    if choice == 1:
        print("Running corpus...")
        runCorpus()
    elif choice == 2:
        print("Running semantic match...")
        semanticMatch()
    elif choice == 3:
        print("Running basic match...")
        basicMatch()
    else:
        print("Invalid choice. Please try again.")